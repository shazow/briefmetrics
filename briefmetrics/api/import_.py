import string
import time
import stripe
from sqlalchemy import orm

from briefmetrics import model, lib
from briefmetrics.lib import payment, pricing
from . import account as api_account


Session = model.Session


def _parse_csv(fp):
    for line in fp:
        if line.startswith('#'):
            continue

        yield map(string.strip, line.split('\t'))

def from_appengine(accounts_csv, subscriptions_csv):
    accounts = list(_parse_csv(accounts_csv))
    subs = list(_parse_csv(subscriptions_csv))

    for s in subs:
        email = s[1][2:-2]
        for a in accounts:
            if a[1] == email:
                a += [s]

    accounts = sorted(accounts, key=lambda o: o[3])

    for _, email, email_token, time_created, token_access, token_expire, token_refresh, sub in accounts:
        _, _, time_next, ga_account_id, ga_internal_id, ga_id, ga_web_property_id, ga_website_url = sub

        token = {
            u'access_token': unicode(token_access),
            u'expires_at': -1,
            u'expires_in': -1,
            u'refresh_token': unicode(token_refresh),
            u'token_type': u'Bearer'}

        user = api_account.get_or_create(email=email, token=token)

        remote_data = {
            u'accountId': unicode(ga_account_id),
            u'id': unicode(ga_id),
            u'internalWebPropertyId': unicode(ga_internal_id),
            u'webPropertyId': unicode(ga_web_property_id),
            u'websiteUrl': unicode(ga_website_url),
            u'kind': u'analytics#profile',
            u'name': u'',
            u'type': u'WEB',
         }

        report = model.Report.create(
            account_id=user.account.id, # XXX: accounts
            remote_data=remote_data,
            remote_id=str(ga_id),
        )

        model.Subscription.create(user=user, report=report)


def backfill_invited_by():
    q = Session.query(model.User).filter_by(plan_id='recipient')
    q = q.options(orm.joinedload_all('reports.account'))

    for user in q:
        if not user.reports:
            print "No active report for user: [%s] %s" % (user.id, user.display_name)
            continue

        report = user.reports[0]
        user.invited_by_user_id = report.account.user_id
        print "Linking user invite: [%s] %s -> [%s] %s" % (user.id, user.display_name, report.account.user_id, report.account.display_name)


def backfill_account_remote_id():
    q = Session.query(model.Account).filter_by(service='stripe')

    i = -1
    for i, account in enumerate(q):
        account.remote_id = account.oauth_token.get('stripe_user_id')

    if i >= 0:
        print "Backfilled {} Stripe account remote ids.".format(i+1)


def backfill_stripe_to_google(request, stripe_account, ga_tracking_id, since_datetime=None, limit=100, pretend=True):
    stripe_query = api_account.query_service(request, stripe_account)
    params = {
        'type': 'invoice.payment_succeeded',
        'limit': str(limit),
        'created[gte]': int(time.mktime(since_datetime.timetuple())),
    }
    items = stripe_query.get_paged('https://api.stripe.com/v1/events', params=params)

    for data in items:
        t = stripe_query.extract_transaction(data)
        lib.service.registry['google'].inject_transaction(ga_tracking_id, t, pretend=pretend)

    print "Backfilled {} Stripe ecommerce transactions to GA.".format(len(items))



def sync_plans(pretend=True, include_hidden=False):
    if pretend:
        print "(Running in pretend mode)"

    local_plans = set(key for key, plan in pricing.Plan.all() if not plan.is_hidden)

    r = stripe.Plan.all()
    for plan in r.data:
        try:
            local_plan_id = plan.id.split('briefmetrics_', 1)[1]
        except IndexError:
            print "Invalid plan prefix: %s" % plan.id
            continue

        if local_plan_id not in local_plans:
            print "Plan missing locally: {}".format(local_plan_id)
            continue

        local_plans.remove(local_plan_id)
        local_plan = pricing.Plan.get(local_plan_id)

        if plan.amount != local_plan.stripe_amount or plan.interval != local_plan.stripe_interval:
            print "Plan discrepency for '{stripe.id}': Remote {stripe.amount}/{stripe.interval}, local {plan.stripe_amount}/{plan.stripe_interval}".format(
                plan=local_plan,
                stripe=plan,
            )

    for plan_id in local_plans:
        print "Plan missing remotely: {}".format(plan_id)
        if pretend:
            continue

        plan = pricing.Plan.get(plan_id)
        stripe.Plan.create(
            id=payment.StripePayment._plan_key(plan_id),
            amount=plan.stripe_amount,
            interval=plan.stripe_interval,
            name='Briefmetrics: %s' % plan.name,
            currency='usd',
            statement_description='Briefmetrics',
        )


def sync_customers(pretend=True, only_plan=False):
    if pretend:
        print "(Running in pretend mode)"

    stripe_users = [u for u in model.User.all() if u.stripe_customer_id]

    for user in stripe_users:
        description = 'Briefmetrics User: %s' % user.email
        metadata = {'user_id': user.id}
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.description = description
        customer.metadata = metadata
        customer.email = user.email

        set_plan = False
        if user.num_remaining is None:
            subscriptions = customer.subscriptions.all()
            set_plan = user.plan_id
            if not subscriptions.count:
                print "Plan missing: %r -> %s" % (user, user.plan_id)
            elif subscriptions.count > 1:
                print "Too many plans: %r -> %s -> %s" % (user, user.plan_id, ', '.join(d.plan.id for d in subscriptions.data))
            elif subscriptions.data[0].plan.id != payment.StripePayment._plan_key(user.plan_id):
                print "Wrong plan: %r -> %s -> %s" % (user, user.plan_id, ', '.join(d.plan.id for d in subscriptions.data))
            else:
                set_plan = False

        if pretend:
            continue

        print "Setting customer: {}".format(description)
        if set_plan:
            print "  Updating plan: {}".format(user.plan_id)
            customer.update_subscription(plan=payment.StripePayment._plan_key(user.plan_id))

        if only_plan:
            continue

        customer.save()

    print "Updated {} users.".format(len(stripe_users))
