package weemetrics

import (
	"appengine/datastore"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"github.com/gorilla/schema"
	"github.com/xeonx/timeago"
	"log"
	"net/http"
	"time"
	api "weemetrics/api"
	model "weemetrics/model"
)

var FormDecoder = schema.NewDecoder()

// View handlers

func IndexHandler(c Controller) {
	if c.UserId == 0 {
		c.Render("templates/base.html", "templates/login.html")
		return
	}

	account, accountKey, err := api.Account.Get(c.AppContext, c.UserId)
	if err == datastore.ErrNoSuchEntity {
		api.Account.LogoutUser(c.Session)
		c.Session.AddFlash("Session expired.")
		c.Session.Save(c.Request, c.ResponseWriter)
		c.Render("templates/base.html", "templates/login.html")
		return
	} else if err != nil {
		c.Error(err)
		return
	}

	subscription, _, _ := api.Subscription.Get(c.AppContext, accountKey)
	if subscription == nil {
		c.Session.AddFlash("Choose website.")
		c.Session.Save(c.Request, c.ResponseWriter)
		http.Redirect(c.ResponseWriter, c.Request, "/settings", http.StatusSeeOther)
		return
	}

	if subscription.NextUpdate.After(time.Now()) {
		c.TemplateContext["NextUpdate"] = timeago.English.Format(subscription.NextUpdate)
		c.AppContext.Infof("Next update: %s", time.Now())
	}

	c.TemplateContext["Subscription"] = subscription
	c.TemplateContext["Account"] = account
	c.Render("templates/base.html", "templates/index.html")
}

func AccountConnectHandler(c Controller) {
	token, err := c.OAuthTransport.Exchange(c.Request.FormValue("code"))
	if err != nil {
		c.Error(err)
		return
	}

	log.Println("Exchanged token:", token)

	client := c.OAuthTransport.Client()

	oauthApi, err := oauth2.New(client)
	if err != nil {
		c.Error(err)
		return
	}

	tokenInfo, err := oauthApi.Userinfo.Get().Do()
	if err != nil {
		c.Error(err)
		return
	}

	account := model.Account{
		Email:       tokenInfo.Email,
		Token:       *token,
		TimeCreated: time.Now(),
	}

	key, err := api.Account.Create(c.AppContext, account)
	if err != nil {
		c.Error(err)
		return
	}

	log.Println("Saving user into session: ", key.IntID())

	api.Account.LoginUser(c.Session, key.IntID())
	c.SessionSave()

	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func AccountLoginHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, OAuthConfig.AuthCodeURL(""), http.StatusSeeOther)
		return
	}

	account, _, err := api.Account.Get(c.AppContext, c.UserId)
	if err != nil || account.Token.RefreshToken != "" {
		http.Redirect(c.ResponseWriter, c.Request, OAuthConfig.AuthCodeURL(""), http.StatusSeeOther)
		return
	}

	forceLoginConfig := oauth.Config(OAuthConfig)
	forceLoginConfig.ApprovalPrompt = "force"
	http.Redirect(c.ResponseWriter, c.Request, forceLoginConfig.AuthCodeURL(""), http.StatusSeeOther)
}

func AccountLogoutHandler(c Controller) {
	api.Account.LogoutUser(c.Session)
	c.Session.AddFlash("Goodbye.")
	c.SessionSave()

	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func SettingsHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, "/account/login", http.StatusForbidden)
		return
	}

	account, accountKey, err := api.Account.Get(c.AppContext, c.UserId)
	if err != nil {
		c.Error(err)
		return
	}

	// Is there a form submission?
	c.Request.ParseForm()
	analyticsProfile := new(model.AnalyticsProfile)
	err = FormDecoder.Decode(analyticsProfile, c.Request.Form)

	if err == nil && analyticsProfile.ProfileId != "" {
		sub := model.Subscription{
			Emails:  []string{account.Email},
			Profile: *analyticsProfile,
		}

		// TODO: Verify analyticsProfile is valid per account?
		// TODO: Fill analyticsProfile.WebsiteUrl
		_, err := api.Subscription.Create(c.AppContext, accountKey, sub)
		if err != nil {
			c.Error(err)
			return
		}

		c.Session.AddFlash("Saved settings.")
		c.SessionSave()
		http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
		return
	}

	c.OAuthTransport.Token = &account.Token
	client := c.OAuthTransport.Client()
	analyticsClient, err := analytics.New(client)
	if err != nil {
		c.Error(err)
		return
	}

	analyticsApi := api.AnalyticsApi{
		AppContext: c.AppContext,
		Client:     analyticsClient,
	}

	result := new(analytics.Profiles)
	//err = analyticsApi.Cache("profiles:" + accountKey.StringID(), analyticsApi.Profiles, &result)
	result, err = analyticsApi.Profiles()
	if err != nil {
		c.Error(err)
		return
	}

	c.TemplateContext["AnalyticsProfiles"] = result.Items
	c.Render("templates/base.html", "templates/settings.html")
}

func ReportHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, "/account/login", http.StatusForbidden)
		return
	}

	account, accountKey, err := api.Account.Get(c.AppContext, c.UserId)
	if err != nil {
		c.Error(err)
		return
	}

	subscription, _, _ := api.Subscription.Get(c.AppContext, accountKey)
	if subscription == nil {
		http.Redirect(c.ResponseWriter, c.Request, "/settings", http.StatusSeeOther)
		return
	}

	c.OAuthTransport.Token = &account.Token
	client := c.OAuthTransport.Client()
	analyticsClient, err := analytics.New(client)
	if err != nil {
		c.Error(err)
		return
	}

	const dateFormat = "2006-01-02"
	startDate := time.Now().Add(-24 * 3 * time.Hour) // TODO: Previous Sunday
	analyticsApi := api.AnalyticsApi{
		AppContext: c.AppContext,
		Client:     analyticsClient,
		ProfileId:  subscription.Profile.ProfileId,
		DateStart:  startDate.Add(-24 * 6 * time.Hour).Format(dateFormat),
		DateEnd:    startDate.Format(dateFormat),
	}

	// TODO: Make async
	referrerData := new(analytics.GaData)
	if err = analyticsApi.Cache("referrers", analyticsApi.Referrers, referrerData); err != nil {
		c.Error(err)
		return
	}

	pageData := new(analytics.GaData)
	if err = analyticsApi.Cache("topPages", analyticsApi.TopPages, pageData); err != nil {
		c.Error(err)
		return
	}

	socialData := new(analytics.GaData)
	if err = analyticsApi.Cache("socialReferrers", analyticsApi.SocialReferrers, socialData); err != nil {
		c.Error(err)
		return
	}

	summaryData := new(analytics.GaData)
	if err = analyticsApi.Cache("summary", analyticsApi.Summary, summaryData); err != nil {
		c.Error(err)
		return
	}

	c.TemplateContext["Profile"] = subscription.Profile
	c.TemplateContext["AnalyticsApi"] = analyticsApi
	c.TemplateContext["DataReferrers"] = referrerData.Rows
	c.TemplateContext["DataSocial"] = socialData.Rows
	c.TemplateContext["DataTopPages"] = pageData.Rows
	c.TemplateContext["DataSummary"] = summaryData.Rows

	c.Render("templates/base.html", "templates/report.html")
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

	// TODO: Implement "/api" handler
}
