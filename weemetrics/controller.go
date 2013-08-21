package weemetrics

import (
	"appengine"
	"appengine/urlfetch"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"github.com/gorilla/sessions"
	"net/http"
	"strings"
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

var OAuthConfig = oauth.Config{
	RedirectURL: "http://localhost:8080/account/connect",
	Scope:       strings.Join(scopes, " "),
	AuthURL:     "https://accounts.google.com/o/oauth2/auth",
	TokenURL:    "https://accounts.google.com/o/oauth2/token",
	AccessType:  "offline",
}

type Controller struct {
	Request        *http.Request
	ResponseWriter http.ResponseWriter
	Session        *sessions.Session
	Context        appengine.Context
	Transport      *urlfetch.Transport
	OAuthTransport *oauth.Transport
	UserId         int64
}

func (c *Controller) SessionSave() {
	c.Session.Save(c.Request, c.ResponseWriter)
}

func AddController(pattern string, f func(Controller)) {
	// Wrap controller function with instantiated Controller object for the first parameter.
	http.HandleFunc(pattern, func(w http.ResponseWriter, r *http.Request) {
		session, _ := sessionStore.Get(r, sessionName)
		context := appengine.NewContext(r)

		transport := &urlfetch.Transport{
			Context: context,
		}
		oauthTransport := &oauth.Transport{
			Config:    &OAuthConfig,
			Transport: transport,
		}

		controller := Controller{
			Request:        r,
			ResponseWriter: w,
			Session:        session,
			Context:        context,
			Transport:      transport,
			OAuthTransport: oauthTransport,
			UserId:         getUser(session),
		}

		f(controller)
	})
}
