stripe_account = model.Account.all()[1]
ga_tracking_id = model.Report.all()[0].remote_data.get('webPropertyId')
import datetime
since_datetime = datetime.datetime.now().replace(day=15)
r = api.import_.backfill_stripe_to_google(request, stripe_account, ga_tracking_id, since_datetime=since_datetime, pretend=True)

