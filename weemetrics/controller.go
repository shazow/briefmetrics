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
	"path/filepath"
	api "weemetrics/api"
	model "weemetrics/model"
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

func TemplateReplace(s string, replace string, with string) string {
	r := strings.Replace(s, replace, with, -1)
	return r
}

func TemplatePermalink(report string, profile model.AnalyticsProfile, analyticsApi api.AnalyticsApi) string {
	r := "https://www.google.com/analytics/web/#report/" + report
	r += "/a" + profile.AccountId + "w" + profile.InternalWebPropertyId + "p" + profile.ProfileId + "/?"

	if analyticsApi.DateStart != "" {
		r += "_u.date00=" + strings.Replace(analyticsApi.DateStart, "-", "", -1) + "&"
	}
	if analyticsApi.DateEnd != "" {
		r += "_u.date01=" + strings.Replace(analyticsApi.DateEnd, "-", "", -1) + "&"
	}

	return r
}

var templateFuncs = template.FuncMap{
	"replace":   TemplateReplace,
	"permalink": TemplatePermalink,
}

func (c *Controller) SessionSave() {
	c.Session.Save(c.Request, c.ResponseWriter)
}

func (c *Controller) Render(filenames ...string) {
	c.TemplateContext["Messages"] = c.Session.Flashes()
	c.SessionSave()

	// TODO: Cache templates?
	rootName := filepath.Base(filenames[0])
	t := template.Must(template.New(rootName).Funcs(templateFuncs).ParseFiles(filenames...))
	err := t.ExecuteTemplate(c.ResponseWriter, rootName, c.TemplateContext)
	if err != nil {
		c.Error(err)
		return
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
