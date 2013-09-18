package model

import (
	"appengine"
	"appengine/datastore"
	"code.google.com/p/goauth2/oauth"
	"time"
	"regexp"
)

var reHumanUrl = regexp.MustCompile(`^(\w*://)?(www\.)?(.+)/?$`)

type Account struct {
	Email       string
	EmailToken  string
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

func (p AnalyticsProfile) UrlID() string {
	return "a" + p.AccountId + "w" + p.InternalWebPropertyId + "p" + p.ProfileId
}

func (p AnalyticsProfile) HumanWebsiteUrl() string {
	return reHumanUrl.ReplaceAllString(p.WebsiteUrl, "$3")
}

type Subscription struct {
	Emails     []string
	NextUpdate time.Time
	Profile    AnalyticsProfile
}

type TokenCache struct {
	Key     *datastore.Key
	Account Account
	Context appengine.Context
}

func (c TokenCache) Token() (*oauth.Token, error) {
	return &c.Account.Token, nil
}

func (c TokenCache) PutToken(token *oauth.Token) error {
	c.Account.Token = *token
	_, err := datastore.Put(c.Context, c.Key, &c.Account)
	c.Context.Debugf("Refreshed token: ", c.Account.Email)
	return err
}
