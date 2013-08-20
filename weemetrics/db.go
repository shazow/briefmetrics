package weemetrics

import (
	"appengine"
	"appengine/datastore"
	"code.google.com/p/goauth2/oauth"
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
	r := make([]Account, 0, 1)

	q := datastore.NewQuery("Account").
		Filter("Email =", account.Email).
		Limit(1)

	var key *datastore.Key
	if keys, err := q.GetAll(context, &r); err != nil {
		key = datastore.NewIncompleteKey(context, "Account", nil)
	} else {
		key = keys[0]
	}

	log.Println("newAccount: saving", key.IntID())

	fn := func(context appengine.Context) error {
		err := datastore.Get(context, key, &account)
		if err == datastore.ErrNoSuchEntity {
			key, err = datastore.Put(context, key, account)
		}
		return err
	}

	log.Println("newAccount: returning", key.IntID())
	return key, datastore.RunInTransaction(context, fn, nil)
}

func getAccount(context appengine.Context, id int64) (*Account, error) {
	key := datastore.NewKey(context, "Account", "", id, nil)
	account := new(Account)
	return account, datastore.Get(context, key, account)
}
