package model

import (
	"code.google.com/p/goauth2/oauth"
	"time"
)

type Account struct {
	Email         string
	Token         oauth.Token
	TimeCreated   time.Time
	TimeProcessed time.Time
}
