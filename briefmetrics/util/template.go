package util

import (
	"github.com/dustin/go-humanize"
	"github.com/xeonx/timeago"
	"html/template"
	"io"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// Template FuncMap:

var timeagoNoPrefix = timeago.Config(timeago.English)

type DateBounder interface {
	UrlDateBoundary() string
}

type AnalyticsID interface {
	UrlID() string
}

func TemplateReplace(s string, replace string, with string) string {
	r := strings.Replace(s, replace, with, -1)
	return r
}

func TemplatePermalink(report string, profile AnalyticsID, d DateBounder) string {
	return "https://www.google.com/analytics/web/#report/" + report + "/" + profile.UrlID() + "/?" + d.UrlDateBoundary()
}

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

func TemplateLinkify(s string) template.HTML {
	url := s
	if !strings.Contains(url, "://") {
		url = "http://" + url
	}

	return template.HTML("<a href=\"" + url + "\">" + s + "</a>")
}

func TemplateHighlight(s string) template.HTML {
	return template.HTML("<span class=\"highlight\">" + s + "</span>")
}

var templateFuncs = template.FuncMap{
	"replace":   TemplateReplace,
	"permalink": TemplatePermalink,
	"timeago":   TemplateTimeago,
	"comma":     TemplateComma,
	"linkify":   TemplateLinkify,
	"highlight":   TemplateHighlight,
}

// Render helpers:

func RenderTo(out io.Writer, templateContext map[string]interface{}, filenames ...string) error {
	// TODO: Cache templates?
	rootName := filepath.Base(filenames[0])
	t := template.Must(template.New(rootName).Funcs(templateFuncs).ParseFiles(filenames...))
	return t.ExecuteTemplate(out, rootName, templateContext)
}

func init() {
	timeagoNoPrefix.PastSuffix, timeagoNoPrefix.FuturePrefix = "", ""

}
