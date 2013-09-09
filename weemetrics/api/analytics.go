package api

import (
	"appengine"
	"appengine/memcache"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
)

type AnalyticsApi struct {
	*Api
	AppContext appengine.Context
	OAuth      *oauth.Config
	Client     *analytics.Service
	ProfileId  string
	DateStart  string
	DateEnd    string
}

func (a *AnalyticsApi) Cache(keySuffix string, f func() (*analytics.GaData, error), result *analytics.GaData) error {
	key := a.ProfileId + ":" + a.DateStart + ":" + keySuffix

	_, err := memcache.Gob.Get(a.AppContext, key, result)
	if err == nil {
		return nil
	}

	r, err := f()
	if err != nil {
		return err
	}

	*result = *r
	a.AppContext.Debugf("Saving cache to:", key)
	err = memcache.Gob.Set(a.AppContext, &memcache.Item{
		Key:    key,
		Object: result,
		// Expiration: cacheExpiration,
	})
	if err != nil {
		a.AppContext.Errorf("Failed to cache key [%s] because:", key, err)
	}
	return nil
}

func (a *AnalyticsApi) Profiles() (r *analytics.Profiles, err error) {
	return a.Client.Management.Profiles.List("~all", "~all").Do()
}

func (a *AnalyticsApi) Summary() (r *analytics.GaData, err error) {
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:pageviews,ga:uniquePageviews,ga:timeOnSite")
		//Dimensions("ga:date")
	return q.Do()
}

func (a *AnalyticsApi) Referrers() (r *analytics.GaData, err error) {
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:visits").
		Dimensions("ga:fullReferrer").
		Filters("ga:medium==referral").
		Sort("-ga:visits").
		MaxResults(10)
	return q.Do()
}

func (a *AnalyticsApi) TopPages() (r *analytics.GaData, err error) {
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:pageviews").
		Dimensions("ga:pagePath").
		Sort("-ga:pageviews").
		MaxResults(10)
	return q.Do()
}

func (a *AnalyticsApi) SocialReferrers() (r *analytics.GaData, err error) {
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:visits").
		Dimensions("ga:socialNetwork").
		Sort("-ga:visits").
		MaxResults(5)
	return q.Do()
}
