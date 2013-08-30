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

type Subscription struct {
	AccountId     string
	WebPropertyId string
	ProfileId     string
	Emails        []string
	NextUpdate    time.Time
}
