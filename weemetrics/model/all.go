package model

import (
	"code.google.com/p/goauth2/oauth"
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
