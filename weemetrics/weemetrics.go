package weemetrics

import (
	"appengine"
	"appengine/urlfetch"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"fmt"
	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"log"
	"net/http"
	"strings"
	"time"
)

const (
	sessionSecret = "FaZFic5qKlzhXungl1Yw7ScbRtFl2ZW2" // XXX: Make secret
	sessionName   = "weemetrics"
)

var sessionStore = sessions.NewCookieStore([]byte(sessionSecret))

var scopes = []string{
	oauth2.UserinfoEmailScope,
	analytics.AnalyticsReadonlyScope,
}

var config = oauth.Config{
	RedirectURL: "http://localhost:8080/account/connect",
	Scope:       strings.Join(scopes, " "),
	AuthURL:     "https://accounts.google.com/o/oauth2/auth",
	TokenURL:    "https://accounts.google.com/o/oauth2/token",
	AccessType:  "offline",
}

// View handlers

func IndexHandler(w http.ResponseWriter, r *http.Request) {
	session, _ := sessionStore.Get(r, sessionName)
	userId := getUser(session)

	if userId == 0 {
		fmt.Fprint(w, "<a href=\"/account/login\">Sign in</a>?")
		return
	}

	context := appengine.NewContext(r)
	account, err := getAccount(context, userId)
	if err != nil {
		log.Println("Tried to fetch", userId, "got", err)

		// Invalid key, delete
		logoutUser(session)
		session.Save(r, w)

		fmt.Fprint(w, "Session expired. <a href=\"/account/login\">Sign in</a>?")
		return
	}

	fmt.Fprint(w, "Hello, ", account.Email)
}

func AccountConnectHandler(w http.ResponseWriter, r *http.Request) {
	context := appengine.NewContext(r)

	// TODO: Check state? r.FormValue("state")
	transport := &oauth.Transport{
		Config: &config,
		Transport: &urlfetch.Transport{
			Context: context,
		},
	}

	token, err := transport.Exchange(r.FormValue("code"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println("Exchanged token:", token)

	client := transport.Client()

	oauthApi, err := oauth2.New(client)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	tokenInfo, err := oauthApi.Userinfo.Get().Do()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	account := Account{
		Email:       tokenInfo.Email,
		Token:       *token,
		TimeCreated: time.Now(),
	}

	key, err := newAccount(context, account)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Println("Saving user into session: ", key.IntID())

	session, _ := sessionStore.Get(r, sessionName)
	loginUser(session, key.IntID())
	session.Save(r, w)

	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func AccountLoginHandler(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, config.AuthCodeURL(""), http.StatusSeeOther)
}

func AccountLogoutHandler(w http.ResponseWriter, r *http.Request) {
	session, _ := sessionStore.Get(r, sessionName)
	logoutUser(session)
	session.Save(r, w)

	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func SettingsHandler(w http.ResponseWriter, r *http.Request) {
	context := appengine.NewContext(r)

	session, _ := sessionStore.Get(r, sessionName)
	userId := getUser(session)

	if userId == 0 {
		http.Redirect(w, r, "/account/login", http.StatusForbidden)
		return
	}

	account, err := getAccount(context, userId)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	transport := &oauth.Transport{
		Config: &config,
		Transport: &urlfetch.Transport{
			Context: context,
		},
		Token: &account.Token,
	}
	client := transport.Client()

	analyticsApi, err := analytics.New(client)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	result, err := analyticsApi.Management.Accounts.List().Do()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	fmt.Fprintf(w, "Hello, %+v", result)
}

func ReportHandler(w http.ResponseWriter, r *http.Request) {
	session, _ := sessionStore.Get(r, sessionName)
	userId := getUser(session)

	if userId == 0 {
		http.Redirect(w, r, "/account/login", http.StatusForbidden)
		return
	}
}

func init() {
	config.ClientId = "909659267876-k6qlc3i22rpsfj9t7r1998tvt9l7ghms.apps.googleusercontent.com" // XXX: Fetch from file
	config.ClientSecret = "FB9ocrxz9witysKA8tcMnMh5"                                             // XXX: Fetch from file

	router := mux.NewRouter()
	router.HandleFunc("/", IndexHandler)
	router.HandleFunc("/account/connect", AccountConnectHandler)
	router.HandleFunc("/account/login", AccountLoginHandler)
	router.HandleFunc("/account/logout", AccountLogoutHandler)
	router.HandleFunc("/settings", SettingsHandler)
	router.HandleFunc("/report", ReportHandler)

	http.Handle("/", router)
}
