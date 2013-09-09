package model

import (
	"code.google.com/p/goauth2/oauth"
	"appengine"
	"appengine/datastore"
	"time"
)

type Account struct {
	Email       string
	Token       oauth.Token
	TimeCreated time.Time
}

type AnalyticsProfile struct {
	AccountId             string
	WebPropertyId         string
	ProfileId             string
	InternalWebPropertyId string
	WebsiteUrl            string
}

type Subscription struct {
	Emails     []string
	NextUpdate time.Time
	Profile    AnalyticsProfile
}


type TokenCache struct {
	Key *datastore.Key
	Account Account
	Context appengine.Context
}

func (c TokenCache) Token() (*oauth.Token, error) {
	return &c.Account.Token, nil
}

func (c TokenCache) PutToken(token *oauth.Token) (error) {
	c.Account.Token = *token
	_, err := datastore.Put(c.Context, c.Key, &c.Account)
	c.Context.Debugf("Refreshed token: ", c.Account.Email)
	return err
}
