package briefmetrics

import (
	"appengine"
	"appengine/urlfetch"
	api "briefmetrics/api"
	util "briefmetrics/util"
	"code.google.com/p/goauth2/oauth"
	"github.com/BurntSushi/toml"
	"github.com/gorilla/sessions"
	"github.com/mattbaird/gochimp"
	"encoding/gob"
	"net/http"
)

type Config struct {
	SessionSecret string
	SessionName   string

	AnalyticsAPI oauth.Config
	MandrillAPI  gochimp.MandrillAPI
}

func (c Config) Analytics() oauth.Config {
	return oauth.Config(c.AnalyticsAPI)
}

func (c Config) Mandrill(transport *urlfetch.Transport) gochimp.MandrillAPI {
	mandrill := gochimp.MandrillAPI(c.MandrillAPI)
	mandrill.Transport = transport
	return mandrill
}

var AppConfig Config

var SessionStore *sessions.CookieStore

type Controller struct {
	Request         *http.Request
	ResponseWriter  http.ResponseWriter
	Session         *sessions.Session
	TemplateContext map[string]interface{}

	// AppEngine-specific
	AppContext     appengine.Context
	Transport      *urlfetch.Transport
	OAuthTransport *oauth.Transport

	// App-specific
	UserId int64
}

func (c *Controller) SessionSave() {
	c.Session.Save(c.Request, c.ResponseWriter)
}

func (c *Controller) Render(filenames ...string) {
	c.TemplateContext["Messages"] = c.Session.Flashes()
	c.SessionSave()

	err := util.RenderTo(c.ResponseWriter, c.TemplateContext, filenames...)
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
		session, _ := SessionStore.Get(r, AppConfig.SessionName)
		appContext := appengine.NewContext(r)

		transport := &urlfetch.Transport{
			Context: appContext,
		}
		oauthConfig := oauth.Config(AppConfig.AnalyticsAPI)
		oauthTransport := &oauth.Transport{
			Config:    &oauthConfig,
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

var ConfigPaths = []string{".dev/config.toml", "config.toml"}

func init() {
	var lastError error
	for _, path := range ConfigPaths {
		if _, lastError = toml.DecodeFile(path, &AppConfig); lastError == nil {
			break
		}
	}

	if lastError != nil {
		panic("Failed to load config.")
	}

	SessionStore = sessions.NewCookieStore([]byte(AppConfig.SessionSecret))

	// Swap out MandrillAPI object with initialized one
	m, _ := gochimp.NewMandrill(AppConfig.MandrillAPI.Key)
	AppConfig.MandrillAPI = *m

	gob.Register(Config{})
}
