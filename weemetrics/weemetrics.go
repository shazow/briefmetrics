package weemetrics

import (
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"fmt"
	"log"
	"net/http"
	"time"
)

// View handlers

func IndexHandler(c Controller) {
	if c.UserId == 0 {
		c.Render("templates/base.html", "templates/index.html")
		return
	}

	account, err := getAccount(c.AppContext, c.UserId)
	if err != nil {
		// Invalid key, delete
		logoutUser(c.Session)
		c.Session.Save(c.Request, c.ResponseWriter)

		fmt.Fprint(c.ResponseWriter, "Session expired. <a href=\"/account/login\">Sign in</a>?")
		return
	}

	fmt.Fprint(c.ResponseWriter, "Hello, ", account.Email)
}

func AccountConnectHandler(c Controller) {
	token, err := c.OAuthTransport.Exchange(c.Request.FormValue("code"))
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println("Exchanged token:", token)

	client := c.OAuthTransport.Client()

	oauthApi, err := oauth2.New(client)
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	tokenInfo, err := oauthApi.Userinfo.Get().Do()
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	account := Account{
		Email:       tokenInfo.Email,
		Token:       *token,
		TimeCreated: time.Now(),
	}

	key, err := newAccount(c.AppContext, account)
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println("Saving user into session: ", key.IntID())

	loginUser(c.Session, key.IntID())
	c.SessionSave()

	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func AccountLoginHandler(c Controller) {
	http.Redirect(c.ResponseWriter, c.Request, OAuthConfig.AuthCodeURL(""), http.StatusSeeOther)
}

func AccountLogoutHandler(c Controller) {
	logoutUser(c.Session)
	c.SessionSave()

	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func SettingsHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, "/account/login", http.StatusForbidden)
		return
	}

	account, err := getAccount(c.AppContext, c.UserId)
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	c.OAuthTransport.Token = &account.Token
	client := c.OAuthTransport.Client()

	analyticsApi, err := analytics.New(client)
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	result, err := analyticsApi.Management.Accounts.List().Do()
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	fmt.Fprintf(c.ResponseWriter, "Hello, %+v", result)
}

func ReportHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, "/account/login", http.StatusForbidden)
		return
	}

	account, err := getAccount(c.AppContext, c.UserId)
	if err != nil {
		http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
		return
	}

	fmt.Fprintf(c.ResponseWriter, "Hello, %+v", account)
}

func init() {
	OAuthConfig.ClientId = "909659267876-k6qlc3i22rpsfj9t7r1998tvt9l7ghms.apps.googleusercontent.com" // XXX: Fetch from file
	OAuthConfig.ClientSecret = "FB9ocrxz9witysKA8tcMnMh5"                                             // XXX: Fetch from file

	AddController("/", IndexHandler)
	AddController("/account/connect", AccountConnectHandler)
	AddController("/account/login", AccountLoginHandler)
	AddController("/account/logout", AccountLogoutHandler)
	AddController("/settings", SettingsHandler)
	AddController("/report", ReportHandler)
}
