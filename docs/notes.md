#

user = model.User.get(1)
google_account = user.get_account(service='google')
query = api.account.query_service(request, account=google_account, cache_keys=False)
available_profiles = query.get_profiles()


#

user = model.User.get_by(email='shazow@gmail.com')
stripe_account = user.get_account(service='stripe')
ga_tracking_id = stripe_account.config.get('ga_funnels')[0]
import datetime
since_datetime = datetime.datetime.now().replace(day=2)
r = api.import_.backfill_stripe_to_google(request, stripe_account, ga_tracking_id, since_datetime=since_datetime, pretend=True)
