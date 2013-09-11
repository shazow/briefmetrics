package api

import (
	"bytes"
	"appengine"
	"appengine/datastore"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"github.com/mattbaird/gochimp"
	"time"
	"net/http"
	model "briefmetrics/model"
	util "briefmetrics/util"
)

type ReportApi struct{ *Api }

var Report = ReportApi{}

const dateFormat = "2006-01-02"

func (a *ReportApi) Generate(context appengine.Context, httpClient *http.Client, accountKey *datastore.Key, account *model.Account, subscription *model.Subscription) (*map[string]interface{}, error) {
	analyticsClient, err := analytics.New(httpClient)
	if err != nil {
		return nil, err
	}

	startDate := time.Now().Add(-24 * 3 * time.Hour) // TODO: Previous Sunday
	analyticsApi := AnalyticsApi{
		AppContext: context,
		Client:     analyticsClient,
		ProfileId:  subscription.Profile.ProfileId,
		DateStart:  startDate.Add(-24 * 6 * time.Hour).Format(dateFormat),
		DateEnd:    startDate.Format(dateFormat),
	}

	templateContext := make(map[string]interface{})
	templateContext["Profile"] = subscription.Profile
	templateContext["AnalyticsApi"] = analyticsApi

	numResults := 4
	results := make(chan AnalyticsResult)
	defer close(results)

	go analyticsApi.Cache("referrer", analyticsApi.Referrers, results)
	go analyticsApi.Cache("page", analyticsApi.TopPages, results)
	go analyticsApi.Cache("social", analyticsApi.SocialReferrers, results)
	go analyticsApi.Cache("summary", analyticsApi.Summary, results)

	for ; numResults > 0; numResults-- {
		r := <- results

		if r.Error != nil {
			return nil, r.Error
		}

		templateContext[r.Label + "Data"] = r.GaData
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
		Subject:     "Analytics report",
		Html:        html.String(),
		TrackOpens:  true,
		TrackClicks: true,
		AutoText:    true,
		InlineCss:   true,
	}

	return msg, nil
}
