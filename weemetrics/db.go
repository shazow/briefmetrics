package weemetrics

import (
	"appengine"
	"appengine/datastore"
	"code.google.com/p/goauth2/oauth"
	"github.com/gorilla/sessions"
	"log"
	"time"
)

type Account struct {
	Email         string
	Token         oauth.Token
	TimeCreated   time.Time
	TimeProcessed time.Time
}

func newAccount(context appengine.Context, account Account) (*datastore.Key, error) {
	// Based on Account.Email, get or create the account and return its Key.
	r := make([]Account, 0, 1)

	var returnKey *datastore.Key
	err := datastore.RunInTransaction(context, func(context appengine.Context) error {
		q := datastore.NewQuery("Account").
			Filter("Email =", account.Email).
			Limit(1)

		keys, err := q.GetAll(context, &r)
		if err == nil && len(keys) == 1 {
			returnKey = keys[0]
			log.Println("newAccount: found key", returnKey.IntID())
			return nil
		}

		log.Println("newAccount: key not found.")
		key := datastore.NewIncompleteKey(context, "Account", nil)

		returnKey, err = datastore.Put(context, key, &account)
		log.Println("newAccount: saved to key", returnKey.IntID())

		return err
	}, nil)

	return returnKey, err
}

func getAccount(context appengine.Context, id int64) (*Account, error) {
	key := datastore.NewKey(context, "Account", "", id, nil)
	account := new(Account)
	return account, datastore.Get(context, key, account)
}

// API
// TODO: These should go live elsewhere

func getUser(s *sessions.Session) int64 {
	userId := s.Values["userId"]
	if userId == nil {
		return 0
	}
	return userId.(int64)
}

func loginUser(s *sessions.Session, userId int64) {
	s.Values["userId"] = userId
}

func logoutUser(s *sessions.Session) {
	delete(s.Values, "userId")
}
