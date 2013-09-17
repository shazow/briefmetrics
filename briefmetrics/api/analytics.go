package api

import (
	"appengine"
	"appengine/memcache"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"strings"
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

type AnalyticsResult struct {
	Label  string
	Error  error
	GaData analytics.GaData
}

func (a *AnalyticsApi) Cache(label string, f func() (*analytics.GaData, error), result chan AnalyticsResult) {
	key := a.ProfileId + ":" + a.DateStart + ":" + label

	r := AnalyticsResult{Label: label}
	_, err := memcache.Gob.Get(a.AppContext, key, &r.GaData)
	if err == nil {
		result <- r
		return
	} else if err != memcache.ErrCacheMiss {
		a.AppContext.Errorf("Failed to retrieve cache key [%s] because:", key, err)
	}

	data, err := f()
	r.GaData = *data
	if err != nil {
		r.Error = err
		result <- r
		return
	}

	a.AppContext.Debugf("Saving cache to:", key)
	err = memcache.Gob.Set(a.AppContext, &memcache.Item{
		Key:    key,
		Object: r.GaData,
		// Expiration: cacheExpiration,
	})
	if err != nil {
		a.AppContext.Errorf("Failed to cache key [%s] because:", key, err)
		r.Error = err
	}

	result <- r
}

func (a *AnalyticsApi) Profiles() (r *analytics.Profiles, err error) {
	return a.Client.Management.Profiles.List("~all", "~all").Do()
}

func (a *AnalyticsApi) Summary() (r *analytics.GaData, err error) {
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:pageviews,ga:uniquePageviews,ga:timeOnSite")
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

func (a *AnalyticsApi) UrlDateBoundary() string {
	parts := make([]string, 2)

	if a.DateStart != "" {
		parts = append(parts, "_u.date00=" + strings.Replace(a.DateStart, "-", "", -1))
	}
	if a.DateEnd != "" {
		parts = append(parts, "_u.date01=" + strings.Replace(a.DateEnd, "-", "", -1))
	}

	return strings.Join(parts, "&")
}