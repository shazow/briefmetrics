package api

import (
	"appengine"
	"appengine/datastore"
	"appengine/urlfetch"
	"appengine/delay"
	model "briefmetrics/model"
	util "briefmetrics/util"
	"bytes"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"fmt"
	"github.com/mattbaird/gochimp"
	"time"
	"strconv"
)

type ReportApi struct{ *Api }

var Report = ReportApi{}

const formatDateGa = "20060102"
const formatDateISO = "2006-01-02"
const formatDateHuman = "Monday, January 2"

func reformatHistoricData(data analytics.GaData) (*[][]int, int, error) {
	r := [][]int{
		[]int{},
		[]int{},
	}

	if len(data.Rows) == 0 {
		return &r, 0, nil
	}

	var d time.Time
	var err error
	var total int
	var max int
	var month time.Month
	var currentData *[]int
	i := -1

	for _, row := range data.Rows {
		d, err = time.Parse(formatDateGa, row[0])
		if err != nil {
			return nil, max, err
		}

		if d.Month() != month {
			if total > max {
				max = total
			}
			month = d.Month()
			i += 1
			currentData = &r[i]
			total = 0
		}

		value, err := strconv.Atoi(row[1])
		if err != nil {
			return nil, max, err
		}
		total += value
		*currentData = append(*currentData, total)
	}

	// FIXME: Is this broken?
	if total > max {
		max = total
	}

	return &r, max, nil
}

func (a *ReportApi) Generate(context appengine.Context, sinceTime time.Time, analyticsClient *analytics.Service, accountKey *datastore.Key, account *model.Account, subscription *model.Subscription) (map[string]interface{}, string, error) {
	// Week + Sunday offset
	startDate := sinceTime.Add(-24*7*time.Hour - time.Hour*24*time.Duration(sinceTime.Weekday()))
	endDate := startDate.Add(24 * 6 * time.Hour)

	analyticsApi := AnalyticsApi{
		AppContext: context,
		Client:     analyticsClient,
		ProfileId:  subscription.Profile.ProfileId,
		DateStart:  startDate.Format(formatDateISO),
		DateEnd:    endDate.Format(formatDateISO),
	}

	subject := "Weekly report for " + subscription.Profile.HumanWebsiteUrl()
	templateContext := make(map[string]interface{})
	templateContext["Subject"] = subject
	templateContext["StartDate"] = startDate.Format(formatDateHuman)
	templateContext["NextDate"] = endDate.Add(24 * 9 * time.Hour).Format(formatDateHuman)
	templateContext["Token"] = fmt.Sprintf("%d-%s", accountKey.IntID(), account.EmailToken)
	templateContext["Profile"] = subscription.Profile
	templateContext["AnalyticsApi"] = &analyticsApi

	numResults := 5
	results := make(chan AnalyticsResult)
	defer close(results)

	go analyticsApi.Cache("referrer", analyticsApi.Referrers, results)
	go analyticsApi.Cache("page", analyticsApi.TopPages, results)
	go analyticsApi.Cache("social", analyticsApi.SocialReferrers, results)
	go analyticsApi.Cache("summary", analyticsApi.Summary, results)
	go analyticsApi.Cache("historic", analyticsApi.Historic, results)

	var chart *util.Chart
	for ; numResults > 0; numResults-- {
		r := <-results

		if r.Error != nil {
			return nil, subject, r.Error
		}

		if r.Label == "historic" {
			chartData, max, err := reformatHistoricData(r.GaData)
			if err != nil {
				return nil, subject, err
			}

			chart = &util.Chart{
				Size: "600x200",
				Data: *chartData,
				Max: max,
			}
			continue
		}
		templateContext[r.Label+"Data"] = r.GaData
	}

	lenCurrent := len(chart.Data[1])
	if lenCurrent > len(chart.Data[0]) {
		lenCurrent = len(chart.Data[0])
	}
	templateContext["TotalLast"] = chart.Data[0][len(chart.Data[0])-1]
	templateContext["TotalLastRelative"] = chart.Data[0][lenCurrent]
	templateContext["TotalCurrent"] = chart.Data[1][len(chart.Data[1])-1]
	templateContext["SummaryChartUrl"] = chart.Url()

	return templateContext, subject, nil
}

func (a *ReportApi) Compose(templateContext map[string]interface{}, template string, subject string, subscription *model.Subscription) (*gochimp.Message, error) {
	var html bytes.Buffer

	err := util.RenderTo(&html, templateContext, "templates/email/base.html", template)
	if err != nil {
		return nil, err
	}

	recipients := make([]gochimp.Recipient, len(subscription.Emails))
	for i, email := range subscription.Emails {
		recipients[i].Email = email
	}
	msg := gochimp.Message{
		FromName:    "Briefmetrics",
		FromEmail:   "support@briefmetrics.com",
		To:          recipients,
		BCCAddress:  "debug@briefmetrics.com",
		Subject:     subject,
		Html:        html.String(),
		TrackOpens:  true,
		TrackClicks: true,
		AutoText:    true,
		InlineCss:   true,
	}

	return &msg, nil
}

type APIConfig interface {
	Analytics() oauth.Config
	Mandrill(*urlfetch.Transport) gochimp.MandrillAPI
}

func (a *ReportApi) Send(appContext appengine.Context, apiConfig APIConfig, sinceTime time.Time, accountKey datastore.Key, account model.Account, subscriptionKey datastore.Key, subscription model.Subscription) {
	analyticsApi := AnalyticsApi{
		AppContext: appContext,
	}
	analyticsApi.SetupClient(apiConfig.Analytics(), &accountKey, &account)
	mandrillApi := apiConfig.Mandrill(analyticsApi.Transport)
	var message *gochimp.Message
	var err error

	// TODO: Rewrite this less branchily
	if account.Token.RefreshToken == "" {
		// No refresh token :(
		message, err = Report.Compose(nil, "templates/email/error_auth.html", "Problem with your Briefmetrics account", &subscription)
	} else {
		templateContext, subject, err := Report.Generate(appContext, sinceTime, analyticsApi.Client, &accountKey, &account, &subscription)
		if err != nil {
			appContext.Errorf("api.Report.Send: Failed to generate report [%d]: ", subscriptionKey.IntID(), err)
			return
		}
		if len(templateContext["pageData"].(analytics.GaData).Rows) == 0 {
			// No data :(
			message, err = Report.Compose(templateContext, "templates/email/error_empty.html", subject, &subscription)
		} else {
			message, err = Report.Compose(templateContext, "templates/email/report.html", subject, &subscription)
		}
	}
	if err != nil {
		appContext.Errorf("api.Report.Send: Failed to compose email [%d]: ", subscriptionKey.IntID(), err)
		return
	}

	_, err = mandrillApi.MessageSend(*message, true)
	if err != nil {
		appContext.Errorf("api.Report.Send: Failed to send email [%d]: ", subscriptionKey.IntID(), err)
		return
	}

	// FIXME: Next week Monday, not Sunday!
	// Next update: Next week.
	if subscription.NextUpdate.Year() == 1 {
		subscription.NextUpdate = time.Now().Truncate(time.Hour)
	}
	subscription.NextUpdate = subscription.NextUpdate.Add(time.Hour * 24 * 7)

	_, err = datastore.Put(appContext, &subscriptionKey, &subscription)
	if err != nil {
		appContext.Errorf("api.Report.Send: Failed to reschedule subscription [%d]: ", subscriptionKey.IntID(), err)
		return
	}
}

var ReportAsyncSend = delay.Func("ReportSend", Report.Send)
