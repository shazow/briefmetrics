package util

import (
	"html/template"
	"io"
	"github.com/xeonx/timeago"
	"github.com/dustin/go-humanize"
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

var templateFuncs = template.FuncMap{
	"replace":   TemplateReplace,
	"permalink": TemplatePermalink,
	"timeago":   TemplateTimeago,
	"comma":     TemplateComma,
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
