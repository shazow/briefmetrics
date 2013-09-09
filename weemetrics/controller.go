package weemetrics

import (
	"appengine"
	"appengine/urlfetch"
	"code.google.com/p/goauth2/oauth"
	"github.com/BurntSushi/toml"
	"github.com/dustin/go-humanize"
	"github.com/gorilla/sessions"
	"github.com/mattbaird/gochimp"
	"github.com/xeonx/timeago"
	"html/template"
	"io"
	"net/http"
	"path/filepath"
	"strconv"
	"strings"
	"time"
	api "weemetrics/api"
	model "weemetrics/model"
)

type Config struct {
	SessionSecret string
	SessionName   string

	AnalyticsAPI oauth.Config
	MandrillAPI  gochimp.MandrillAPI
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

var timeagoNoPrefix = timeago.Config(timeago.English)

func TemplateTimeago(seconds string) string {
	remainder, _ := time.ParseDuration(seconds + "s")
	day := time.Hour * 24
	if remainder > day {
		hours := remainder % day
		remainder -= hours
		days := remainder / day
		return strconv.FormatInt(days.Nanoseconds(), 10) + " days and " + hours.String()
	}
	return remainder.String()
}

func TemplateComma(number string) string {
	i, _ := strconv.ParseInt(number, 10, 64)
	return humanize.Comma(i)
}

var templateFuncs = template.FuncMap{
	"replace":   TemplateReplace,
	"permalink": TemplatePermalink,
	"timeago":   TemplateTimeago,
	"comma":     TemplateComma,
}

func (c *Controller) SessionSave() {
	c.Session.Save(c.Request, c.ResponseWriter)
}

func (c *Controller) RenderTo(out io.Writer, filenames ...string) {
	// TODO: Cache templates?
	rootName := filepath.Base(filenames[0])
	t := template.Must(template.New(rootName).Funcs(templateFuncs).ParseFiles(filenames...))
	err := t.ExecuteTemplate(out, rootName, c.TemplateContext)
	if err != nil {
		c.Error(err)
		return
	}
}

func (c *Controller) Render(filenames ...string) {
	c.TemplateContext["Messages"] = c.Session.Flashes()
	c.SessionSave()

	c.RenderTo(c.ResponseWriter, filenames...)
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
	timeagoNoPrefix.PastSuffix, timeagoNoPrefix.FuturePrefix = "", ""

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
}
