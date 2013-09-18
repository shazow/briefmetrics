package api

import (
	"appengine"
	"appengine/datastore"
	"appengine/delay"
	model "briefmetrics/model"
	util "briefmetrics/util"
	"bytes"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"fmt"
	"github.com/mattbaird/gochimp"
	"net/http"
	"time"
)

type ReportApi struct{ *Api }

var Report = ReportApi{}

const formatDateISO = "2006-01-02"
const formatDateHuman = "January 2, 2006"

func (a *ReportApi) Generate(context appengine.Context, sinceTime time.Time, analyticsClient *analytics.Service, accountKey *datastore.Key, account *model.Account, subscription *model.Subscription) (map[string]interface{}, error) {
	// Week + Sunday offset
	startDate := sinceTime.Add(-24*7*time.Hour - time.Hour*24*time.Duration(sinceTime.Weekday()))
	endDate := startDate.Add(24 * 7 * time.Hour)

	analyticsApi := AnalyticsApi{
		AppContext: context,
		Client:     analyticsClient,
		ProfileId:  subscription.Profile.ProfileId,
		DateStart:  startDate.Add(-24 * 6 * time.Hour).Format(formatDateISO),
		DateEnd:    endDate.Format(formatDateISO),
	}

	templateContext := make(map[string]interface{})
	templateContext["Subject"] = "Weekly report for " + subscription.Profile.HumanWebsiteUrl()
	templateContext["Title"] = endDate.Format(formatDateHuman)
	templateContext["Token"] = fmt.Sprintf("%d-%s", accountKey.IntID(), account.EmailToken)
	templateContext["Profile"] = subscription.Profile
	templateContext["AnalyticsApi"] = &analyticsApi

	numResults := 4
	results := make(chan AnalyticsResult)
	defer close(results)

	go analyticsApi.Cache("referrer", analyticsApi.Referrers, results)
	go analyticsApi.Cache("page", analyticsApi.TopPages, results)
	go analyticsApi.Cache("social", analyticsApi.SocialReferrers, results)
	go analyticsApi.Cache("summary", analyticsApi.Summary, results)

	for ; numResults > 0; numResults-- {
		r := <-results

		if r.Error != nil {
			return nil, r.Error
		}

		templateContext[r.Label+"Data"] = r.GaData
	}

	return templateContext, nil
}

func (a *ReportApi) Compose(templateContext map[string]interface{}, subscription *model.Subscription) (*gochimp.Message, error) {
	var html bytes.Buffer

	err := util.RenderTo(&html, templateContext, "templates/base_email.html", "templates/report.html")
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
		Subject:     templateContext["Subject"].(string),
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
	Mandrill(http.RoundTripper) gochimp.MandrillAPI
}

func (a *ReportApi) Send(appContext appengine.Context, apiConfig APIConfig, sinceTime time.Time, accountKey datastore.Key, account model.Account, subscriptionKey datastore.Key, subscription model.Subscription) {
	analyticsApi := AnalyticsApi{
		AppContext: appContext,
	}
	analyticsApi.SetupClient(apiConfig.Analytics(), &accountKey, &account)

	templateContext, err := Report.Generate(appContext, sinceTime, analyticsApi.Client, &accountKey, &account, &subscription)
	if err != nil {
		appContext.Errorf("Delayed: Failed to generate report [%d]: ", subscriptionKey.IntID(), err)
		return
	}
	message, err := Report.Compose(templateContext, &subscription)
	if err != nil {
		appContext.Errorf("Delayed: Failed to compose email [%d]: ", subscriptionKey.IntID(), err)
		return
	}

	mandrill := apiConfig.Mandrill(analyticsApi.Transport)
	_, err = mandrill.MessageSend(*message, true)
	if err != nil {
		appContext.Errorf("Delayed: Failed to send email [%d]: ", subscriptionKey.IntID(), err)
		return
	}

	// Next update: Next week.
	if subscription.NextUpdate.Year() == 1 {
		subscription.NextUpdate = time.Now().Truncate(time.Hour)
	}
	subscription.NextUpdate = subscription.NextUpdate.Add(time.Hour * 24 * 7)

	_, err = datastore.Put(appContext, &subscriptionKey, &subscription)
	if err != nil {
		appContext.Errorf("Delayed: Failed to reschedule subscription [%d]: ", subscriptionKey.IntID(), err)
		return
	}
}

var ReportAsyncSend = delay.Func("ReportSend", Report.Send)
