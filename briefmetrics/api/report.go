package api

import (
	"appengine"
	"appengine/datastore"
	model "briefmetrics/model"
	util "briefmetrics/util"
	"bytes"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"github.com/mattbaird/gochimp"
	"net/http"
	"time"
	"fmt"
)

type ReportApi struct{ *Api }

var Report = ReportApi{}

const formatDateISO = "2006-01-02"
const formatDateHuman = "January 2, 2006"

func (a *ReportApi) Generate(context appengine.Context, httpClient *http.Client, accountKey *datastore.Key, account *model.Account, subscription *model.Subscription) (*map[string]interface{}, error) {
	analyticsClient, err := analytics.New(httpClient)
	if err != nil {
		return nil, err
	}

	// Week + Sunday offset
	startDate := time.Now().Add(-24*7*time.Hour - time.Hour*24*time.Duration(time.Now().Weekday()))
	analyticsApi := AnalyticsApi{
		AppContext: context,
		Client:     analyticsClient,
		ProfileId:  subscription.Profile.ProfileId,
		DateStart:  startDate.Add(-24 * 6 * time.Hour).Format(formatDateISO),
		DateEnd:    startDate.Format(formatDateISO),
	}

	templateContext := make(map[string]interface{})
	templateContext["Title"] = "Week of " + startDate.Format(formatDateHuman)
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

	return &templateContext, nil
}

func (a *ReportApi) Compose(templateContext *map[string]interface{}, subscription *model.Subscription) (*gochimp.Message, error) {
	var html bytes.Buffer

	err := util.RenderTo(&html, *templateContext, "templates/base_email.html", "templates/report.html")
	if err != nil {
		return nil, err
	}

	recipients := make([]gochimp.Recipient, len(subscription.Emails))
	for i, email := range subscription.Emails {
		recipients[i].Email = email
	}
	msg := gochimp.Message{
		FromName:    "Andrey Petrov",
		FromEmail:   "andrey.petrov@shazow.net",
		To:          recipients,
		Subject:     "Briefmetrics weekly report",
		Html:        html.String(),
		TrackOpens:  true,
		TrackClicks: true,
		AutoText:    true,
		InlineCss:   true,
	}

	return &msg, nil
}
