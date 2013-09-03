package api

import (
	"runtime"
	"reflect"
	"time"
	"fmt"
	"appengine"
	"appengine/memcache"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"github.com/shazow/memoizer"
)

const cacheExpiration = time.Hour

type AnalyticsApi struct {
	*AnalyticsApi
	AppContext appengine.Context
	Client     *analytics.Service
	ProfileId  string
	DateStart  string
	DateEnd    string
}

type AppengineCache struct {
	*memoizer.BaseCache
	Context appengine.Context
	DefaultExpiration time.Duration
	KeyPrefix string
}

func (c *AppengineCache) CreateKey(f interface{}, callArgs []interface{}) (key string) {
	fName := runtime.FuncForPC(reflect.ValueOf(f).Pointer()).Name()
	// TODO: Hash function name + args?
	key = c.KeyPrefix + ":" + fName + ":" + fmt.Sprint(callArgs)
	c.Context.Infof("Created key:", key)
	return key
}

func (c *AppengineCache) Get(key string, object *interface{}) error {
	r := reflect.ValueOf(object).Elem()
	_, err := memcache.Gob.Get(c.Context, key, r)

	*object = r.Interface()
	c.Context.Infof(".Get err:", err)
	return err
}
 
func (c *AppengineCache) Set(key string, object interface{}) error {
	memcache.Gob.Set(c.Context, &memcache.Item{
		Key: key,
		Object: object,
		Expiration: c.DefaultExpiration,
	})
	return nil
}

func (a *AnalyticsApi) Referrals() (*analytics.GaData, error) {
	a.AppContext.Infof("Fetching referrals from GA.")
	q := a.Client.Data.Ga.
		Get("ga:"+a.ProfileId, a.DateStart, a.DateEnd, "ga:visits").
		Dimensions("ga:fullReferrer").
		Filters("ga:medium==referral").
		Sort("-ga:visits").
		MaxResults(10)

	return q.Do()
}
