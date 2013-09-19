package util

import (
	"strings"
)

type Chart struct {
	Size   string
	Colors []string
	Data   [][]string
}

func encodeData(d [][]string, width int) string {
	r := "t:"
	for i, row := range d {
		pad := width - len(row)
		if i != 0 {
			r += "|"
		}
		r += strings.Join(row, ",")
		for j := 0; j < pad; j++ {
			r += ",_"
		}
	}
	return r
}

func (c Chart) Url() string {
	return "https://chart.googleapis.com/chart" +
		"?chs=" + c.Size +
		"&cht=ls" +
		"&chco=" + strings.Join(c.Colors, ",") +
		"&chd=" + encodeData(c.Data, len(c.Data[0])) +
		"&chg=-1,-1,0,0" +
		"&chls=1|1" +
		"&chm=B,CAE4F0,0,0,0|B,3072F3,1,0,0,1"
}
