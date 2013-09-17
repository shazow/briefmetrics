package util

import (
	"math/rand"
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
