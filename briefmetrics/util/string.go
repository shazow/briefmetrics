package util

import (
	"math/rand"
	"time"
)

const defaultAlphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

func RandomString(length int, alphabet string) string {
	if alphabet == "" {
		alphabet = defaultAlphabet
	}
	r := make([]byte, length)
	for i := 0; i < length; i++ {
		r[i] = byte(alphabet[rand.Intn(len(alphabet))])
	}
	return string(r)
}

func init() {
	// FIXME: Is there a way to seed in AppEngine without a timing attack?
	rand.Seed(time.Now().UnixNano())
}
