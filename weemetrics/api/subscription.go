package api

import (
	"appengine"
	"appengine/datastore"
	"time"
	model "weemetrics/model"
)

type SubscriptionApi struct{ *Api }

var Subscription = SubscriptionApi{}

func (a *SubscriptionApi) Create(context appengine.Context, accountKey *datastore.Key, subscription model.Subscription) (*datastore.Key, error) {
	// Limit to just one subscription, for meow.
	// TODO: Transaction?
	q := datastore.NewQuery("Subscription").
		Ancestor(accountKey).
		KeysOnly()

	keys, err := q.GetAll(context, nil)
	if err == nil && len(keys) > 0 {
		datastore.DeleteMulti(context, keys)
	}

	key := datastore.NewIncompleteKey(context, "Subscription", accountKey)
	returnKey, err := datastore.Put(context, key, &subscription)

	return returnKey, err
}

func (a *SubscriptionApi) Get(context appengine.Context, accountKey *datastore.Key) (*model.Subscription, *datastore.Key, error) {
	q := datastore.NewQuery("Subscription").
		Ancestor(accountKey).
		Limit(1)

	var subscriptions []model.Subscription
	keys, err := q.GetAll(context, &subscriptions)
	if err == nil && len(keys) > 0 {
		return &subscriptions[0], keys[0], nil
	}

	return nil, nil, err
}

func (a *SubscriptionApi) GetPending(context appengine.Context) ([]model.Subscription, []*datastore.Key, error) {
	q := datastore.NewQuery("Subscription").
		Filter("NextUpdate <=", time.Now())

	var subscriptions []model.Subscription
	keys, err := q.GetAll(context, &subscriptions)

	return subscriptions, keys, err
}
