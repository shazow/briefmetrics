package api

import (
	"appengine"
	"appengine/datastore"
	"github.com/gorilla/sessions"
	"log"
	model "weemetrics/model"
)

var Account = Api{}

func (a *Api) Create(context appengine.Context, account model.Account) (*datastore.Key, error) {
	// Based on model.Account.Email, get or create the account and return its Key.
	// TODO: Prevent dupes
	q := datastore.NewQuery("model.Account").
		Filter("Email =", account.Email).
		Limit(1).
		KeysOnly()

	keys, err := q.GetAll(context, nil)
	if err == nil && len(keys) > 0 {
		log.Println("newmodel.Account: found key", keys[0].IntID())
		return keys[0], nil
	}

	log.Println("newmodel.Account: key not found", err)
	key := datastore.NewIncompleteKey(context, "model.Account", nil)

	returnKey, err := datastore.Put(context, key, &account)
	log.Println("newmodel.Account: saved to key", returnKey.IntID())

	return returnKey, err
}

func (a *Api) Get(context appengine.Context, id int64) (*model.Account, error) {
	key := datastore.NewKey(context, "model.Account", "", id, nil)
	account := new(model.Account)
	return account, datastore.Get(context, key, account)
}

func (a *Api) GetUser(s *sessions.Session) int64 {
	userId := s.Values["userId"]
	if userId == nil {
		return 0
	}
	return userId.(int64)
}

func (a *Api) LoginUser(s *sessions.Session, userId int64) {
	s.Values["userId"] = userId
}

func (a *Api) LogoutUser(s *sessions.Session) {
	delete(s.Values, "userId")
}
