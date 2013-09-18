package briefmetrics

import (
	"appengine/datastore"
	api "briefmetrics/api"
	model "briefmetrics/model"
	util "briefmetrics/util"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"errors"
	"github.com/gorilla/schema"
	"github.com/mattbaird/gochimp"
	"github.com/xeonx/timeago"
	"net/http"
	"strconv"
	"strings"
	"time"
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
		EmailToken:  util.RandomString(16, ""),
		Token:       *token,
		TimeCreated: time.Now(),
	}

	key, err := api.Account.Create(c.AppContext, account)
	if err != nil {
		c.Error(err)
		return
	}

	api.Account.LoginUser(c.Session, key.IntID())
	c.SessionSave()

	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func AccountDisconnectHandler(c Controller) {
	token := c.Request.FormValue("token")
	if token == "" && c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, "/account/login", http.StatusForbidden)
		return
	}

	if c.Request.FormValue("confirmed") == "" {
		c.TemplateContext["Token"] = token
		c.Render("templates/base.html", "templates/disconnect.html")
		return
	}

	var keyId int64
	var confirmToken string
	var err error

	if token != "" {
		parts := strings.Split(token, "-")
		keyId, err = strconv.ParseInt(parts[0], 10, 64)
		if err != nil {
			c.Error(err)
			return
		}
		confirmToken = parts[1]
	} else if c.UserId != 0 {
		keyId = c.UserId
	}

	account, accountKey, err := api.Account.Get(c.AppContext, keyId)
	if err != nil {
		c.Error(err)
		return
	}

	if token != "" && account.EmailToken != confirmToken {
		c.Error(errors.New("Invalid email token."))
		return
	}

	q := datastore.NewQuery("Subscription").
		Ancestor(accountKey).
		KeysOnly()
	subscriptionKeys, err := q.GetAll(c.AppContext, nil)
	if err != nil {
		c.Error(err)
		return
	}

	err = datastore.DeleteMulti(c.AppContext, append(subscriptionKeys, accountKey))
	if err != nil {
		c.Error(err)
		return
	}

	api.Account.LogoutUser(c.Session)
	c.Session.AddFlash("Goodbye.")
	c.SessionSave()
	http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
}

func AccountLoginHandler(c Controller) {
	if c.UserId == 0 {
		http.Redirect(c.ResponseWriter, c.Request, AppConfig.AnalyticsAPI.AuthCodeURL(""), http.StatusSeeOther)
		return
	}

	account, _, err := api.Account.Get(c.AppContext, c.UserId)
	if err != nil || account.Token.RefreshToken != "" {
		http.Redirect(c.ResponseWriter, c.Request, AppConfig.AnalyticsAPI.AuthCodeURL(""), http.StatusSeeOther)
		return
	}

	forceLoginConfig := oauth.Config(AppConfig.AnalyticsAPI)
	forceLoginConfig.ApprovalPrompt = "force"
	http.Redirect(c.ResponseWriter, c.Request, forceLoginConfig.AuthCodeURL(""), http.StatusSeeOther)
}

func AccountLogoutHandler(c Controller) {
	api.Account.LogoutUser(c.Session)
	c.Session.AddFlash("Bye for now.")
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

	c.OAuthTransport.Token = &account.Token
	c.OAuthTransport.Config.TokenCache = model.TokenCache{
		Key:     accountKey,
		Account: *account,
		Context: c.AppContext,
	}
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
	// TODO: Cache
	//err = analyticsApi.Cache("profiles:" + accountKey.StringID(), analyticsApi.Profiles, &result)
	result, err = analyticsApi.Profiles()
	if err != nil {
		c.Error(err)
		return
	}

	// Is there a form submission?
	internalId := c.Request.FormValue("id")

	if internalId != "" {
		analyticsProfile := model.AnalyticsProfile{
			InternalWebPropertyId: internalId,
		}

		// Find the relevant item
		for _, profile := range result.Items {
			if profile.InternalWebPropertyId == internalId {
				analyticsProfile.AccountId = profile.AccountId
				analyticsProfile.WebPropertyId = profile.WebPropertyId
				analyticsProfile.ProfileId = profile.Id
				analyticsProfile.WebsiteUrl = profile.WebsiteUrl
				break
			}
		}

		if analyticsProfile.AccountId == "" {
			c.Error(errors.New("Invalid property id: " + internalId))
			return
		}

		sub := model.Subscription{
			Emails:  []string{account.Email},
			Profile: analyticsProfile,
		}

		_, err := api.Subscription.Create(c.AppContext, accountKey, sub)
		if err != nil {
			c.Error(err)
			return
		}

		c.Session.AddFlash("Created subscription for " + analyticsProfile.WebsiteUrl)
		c.SessionSave()

		// TODO: TaskQueue report for last week.
		http.Redirect(c.ResponseWriter, c.Request, "/", http.StatusSeeOther)
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
	c.OAuthTransport.Config.TokenCache = model.TokenCache{
		Key:     accountKey,
		Account: *account,
		Context: c.AppContext,
	}
	client := c.OAuthTransport.Client()

	templateContext, err := api.Report.Generate(c.AppContext, client, accountKey, account, subscription)
	if err != nil {
		c.Error(err)
		return
	}

	if c.Request.FormValue("send") != "" {
		msg, err := api.Report.Compose(templateContext, subscription)
		if err != nil {
			c.Error(err)
			return
		}

		mandrill := gochimp.MandrillAPI(AppConfig.MandrillAPI)
		mandrill.Transport = c.Transport
		if _, err := mandrill.MessageSend(*msg, true); err != nil {
			c.Error(err)
			return
		}

		c.AppContext.Debugf("Sent report to: ", subscription.Emails)
	}

	util.RenderTo(c.ResponseWriter, templateContext, "templates/base_email.html", "templates/report.html")
}

func CronHandler(c Controller) {
	subscriptions, keys, err := api.Subscription.GetPending(c.AppContext)
	if err != nil {
		c.Error(err)
		return
	}

	now := time.Now()

	// TODO: Use the TaskQueue.
	for i, subscriptionKey := range keys {
		subscription := &subscriptions[i]
		if subscription.NextUpdate.After(now) {
			c.AppContext.Errorf("CronHandler: Premature subscription (NextUpdate: %s), skipping: %s", subscription.NextUpdate, subscriptionKey)
			continue
		}

		account, accountKey, err := api.Account.Get(c.AppContext, subscriptionKey.Parent().IntID())
		c.AppContext.Infof("CronHandler: Processing subscription for account: %s", account.Email)

		// FIXME: Race condition?
		c.OAuthTransport.Token = &account.Token
		c.OAuthTransport.Config.TokenCache = model.TokenCache{
			Key:     accountKey,
			Account: *account,
			Context: c.AppContext,
		}
		client := c.OAuthTransport.Client()

		if err != nil {
			c.AppContext.Errorf("CronHandler: Failed to get account, skipping [%d]:", subscriptionKey.IntID(), err)
			continue
		}

		templateContext, err := api.Report.Generate(c.AppContext, client, accountKey, account, subscription)
		if err != nil {
			c.AppContext.Errorf("CronHandler: Failed to generate report, skipping [%d]:", subscriptionKey.IntID(), err)
			continue
		}

		msg, err := api.Report.Compose(templateContext, subscription)
		if err != nil {
			c.AppContext.Errorf("CronHandler: Failed to compose email, skipping [%d]:", subscriptionKey.IntID(), err)
			continue
		}

		mandrill := gochimp.MandrillAPI(AppConfig.MandrillAPI)
		mandrill.Transport = c.Transport
		if _, err := mandrill.MessageSend(*msg, true); err != nil {
			c.AppContext.Errorf("CronHandler: Failed to send email, skipping [%d]:", subscriptionKey.IntID(), err)
			continue
		}

		// Next update: Next week.
		if subscription.NextUpdate.Year() == 1 {
			subscription.NextUpdate = now.Truncate(time.Hour)
		}
		subscription.NextUpdate = subscription.NextUpdate.Add(time.Hour * 24 * 7)
	}

	if _, err = datastore.PutMulti(c.AppContext, keys, subscriptions); err != nil {
		c.Error(err)
		return
	}
}

func init() {
	AddController("/", IndexHandler)
	AddController("/account/connect", AccountConnectHandler)
	AddController("/account/disconnect", AccountDisconnectHandler)
	AddController("/account/login", AccountLoginHandler)
	AddController("/account/logout", AccountLogoutHandler)
	AddController("/settings", SettingsHandler)
	AddController("/report", ReportHandler)
	AddController("/_cron", CronHandler)

	// TODO: Implement "/api" handler
}
