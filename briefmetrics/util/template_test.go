package util

import (
	"testing"

	api "briefmetrics/api"
	model "briefmetrics/model"
)

func TestReplace(t *testing.T) {
	expected := "_foo_bar_baz_"
	if r := TemplateReplace("-foo-bar-baz-", "-", "_"); r != expected {
		t.Errorf("%s != %s", r, expected)
	}
}

func TestPermalink(t *testing.T) {
	p := model.AnalyticsProfile{
		AccountId:             "000",
		WebPropertyId:         "111",
		ProfileId:             "222",
		InternalWebPropertyId: "333",
	}

	d := api.AnalyticsApi{
		DateStart: "2013-11-29",
		DateEnd:   "2013-11-30",
	}

	expected := "https://www.google.com/analytics/web/#report/foo/a000w333p222/?_u.date00=20131129&_u.date01=20131130"
	if r := TemplatePermalink("foo", p, &d); r != expected {
		t.Errorf("%s != %s", r, expected)
	}
}
