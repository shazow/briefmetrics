user = model.User.get_by(email='shazow@gmail.com')
stripe_account = user.get_account(service='stripe')
ga_tracking_id = next(r.remote_data.get('webPropertyId') for r in user.reports if r.remote_data.get('webPropertyId'))
import datetime
since_datetime = datetime.datetime.now().replace(day=26)
r = api.import_.backfill_stripe_to_google(request, stripe_account, ga_tracking_id, since_datetime=since_datetime, pretend=True)
