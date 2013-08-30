package weemetrics

import (
	"appengine"
	"appengine/urlfetch"
	"code.google.com/p/goauth2/oauth"
	"code.google.com/p/google-api-go-client/analytics/v3"
	"code.google.com/p/google-api-go-client/oauth2/v2"
	"github.com/gorilla/sessions"
	"html/template"
	"net/http"
	"strings"
	api "weemetrics/api"
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
	Request         *http.Request
	ResponseWriter  http.ResponseWriter
	Session         *sessions.Session
	AppContext      appengine.Context
	TemplateContext map[string]interface{}
	Transport       *urlfetch.Transport
	OAuthTransport  *oauth.Transport
	UserId          int64
}

func (c *Controller) SessionSave() {
	c.Session.Save(c.Request, c.ResponseWriter)
}

func (c *Controller) Render(filenames ...string) {
	c.TemplateContext["Messages"] = c.Session.Flashes()
	c.SessionSave()

	// TODO: Cache templates?
	err := template.Must(template.ParseFiles(filenames...)).Execute(c.ResponseWriter, c.TemplateContext)
	if err != nil {
		c.Error(err)
	}
}

func (c *Controller) Error(err error) {
	http.Error(c.ResponseWriter, err.Error(), http.StatusInternalServerError)
}

func AddController(pattern string, f func(Controller)) {
	// Wrap controller function with instantiated Controller object for the first parameter.
	http.HandleFunc(pattern, func(w http.ResponseWriter, r *http.Request) {
		session, _ := sessionStore.Get(r, sessionName)
		appContext := appengine.NewContext(r)

		transport := &urlfetch.Transport{
			Context: appContext,
		}
		oauthTransport := &oauth.Transport{
			Config:    &OAuthConfig,
			Transport: transport,
		}

		templateContext := make(map[string]interface{})

		controller := Controller{
			Request:         r,
			ResponseWriter:  w,
			Session:         session,
			AppContext:      appContext,
			TemplateContext: templateContext,
			Transport:       transport,
			OAuthTransport:  oauthTransport,
			UserId:          api.Account.GetUser(session),
		}

		f(controller)
	})
}
