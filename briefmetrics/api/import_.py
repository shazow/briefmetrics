import string
from sqlalchemy import orm

from briefmetrics import model
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
            account_id=user.account.id,
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
