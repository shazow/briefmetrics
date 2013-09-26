package util

import (
	"strconv"
)

type Chart struct {
	Size   string
	Data   [][]int
	Max    int
}

func encodeData(d [][]int, width int, divisor int) string {
	r := "t:"
	if divisor <= 0 {
		return r
	}

	for i, row := range d {
		pad := width - len(row)
		if i != 0 {
			r += "|"
		}
		for j, value := range row {
			if j != 0 {
				r += ","
			}
			r += strconv.Itoa(value / divisor)
		}
		for j := 0; j < pad; j++ {
			r += ",_"
		}
	}

	weekOffset := len(d[1]) - 7
	weekPad := width - weekOffset - 7
	week := d[1][weekOffset:len(d[1])]
	r += "|_"
	for j := 1; j < weekOffset; j++ {
		r += ",_"
	}
	for _, value := range week {
		r += "," + strconv.Itoa(value / divisor)
	}
	for j := 0; j < weekPad; j++ {
		r += ",_"
	}

	return r
}

func (c Chart) Url() string {
	if c.Max == 0 {
		return ""
	}
	return "https://chart.googleapis.com/chart" +
		"?chs=" + c.Size +
		"&cht=ls" +
		"&chco=ffffff00,9c1a32,ffffff00" +
		"&chd=" + encodeData(c.Data, len(c.Data[0]), c.Max/100) +
		"&chg=-1,-1,0,0" +
		"&chls=1|1" +
		"&chm=B,CE234233,0,0,0|B,CE234277,1,0,0,1|B,CE234240,2,0,0,2"
}
