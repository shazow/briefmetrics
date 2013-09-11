package api

import (
	"appengine"
	"appengine/datastore"
	"github.com/gorilla/sessions"
	model "weemetrics/model"
)

type AccountApi struct{ *AccountApi }

// TODO: Move context+session in here?
var Account = AccountApi{}

func (a *AccountApi) Create(context appengine.Context, account model.Account) (*datastore.Key, error) {
	// Based on model.Account.Email, get or create the account and return its Key.
	// TODO: Prevent dupes
	q := datastore.NewQuery("Account").
		Filter("Email =", account.Email).
		Limit(1).
		KeysOnly()

	keys, err := q.GetAll(context, nil)
	if err == nil && len(keys) > 0 {
		datastore.Put(context, keys[0], &account)
		return keys[0], nil
	}

	key := datastore.NewIncompleteKey(context, "Account", nil)

	returnKey, err := datastore.Put(context, key, &account)

	return returnKey, err
}

func (a *AccountApi) Get(context appengine.Context, id int64) (*model.Account, *datastore.Key, error) {
	key := datastore.NewKey(context, "Account", "", id, nil)
	account := new(model.Account)
	err := datastore.Get(context, key, account)

	return account, key, err
}

func (a *AccountApi) GetUser(s *sessions.Session) int64 {
	userId := s.Values["userId"]
	if userId == nil {
		return 0
	}
	return userId.(int64)
}

func (a *AccountApi) LoginUser(s *sessions.Session, userId int64) {
	s.Values["userId"] = userId
}

func (a *AccountApi) LogoutUser(s *sessions.Session) {
	delete(s.Values, "userId")
}
