package util

import (
	"testing"

	api "briefmetrics/api"
	model "briefmetrics/model"
)

func TestReplace(t *testing.T) {
	if TemplateReplace("-foo-bar-baz-", "-", "_") != "_foo_bar_baz_" {
		t.Errorf("Failed.")
	}
}

func TestPermalink(t *testing.T) {
	p := model.AnalyticsProfile{
		AccountId:             "xxx",
		WebPropertyId:         "yyy",
		ProfileId:             "zzz",
		InternalWebPropertyId: "000",
	}

	d := api.AnalyticsApi{
		DateStart: "2013-11-29",
		DateEnd:   "2013-11-30",
	}

	if TemplatePermalink("foo", p, &d) != "asdf" {
		t.Errorf("Failed.")
	}
}
