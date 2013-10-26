import stripe
from unstdlib import get_many

from briefmetrics import api, model, tasks
from briefmetrics.lib.exceptions import APIControllerError
from briefmetrics.lib import helpers as h

from .api import expose_api, handle_api
from briefmetrics.lib.controller import Controller


@expose_api('settings.subscribe')
def settings_subscribe(request):
    # TODO: Support multiple
    profile_ids = set(int(id) for id in request.params.getall('id') if id)
    user_id = api.account.get_user_id(request, required=True)

    account = model.Account.get_by(user_id=user_id)
    if not account:
        raise APIControllerError("Account does not exist for user: %s" % user_id)

    # Delete removed reports
    num_deleted = 0
    for report in account.reports:
        if report.id in profile_ids:
            profile_ids.discard(report.id)
            continue
        else:
            num_deleted += 1
            report.delete()

    if not profile_ids and num_deleted:
        request.flash('Removed subscription.')
        model.Session.commit()
        return
    elif not profile_ids:
        request.flash('Nothing changed.')
        return

    # TODO: Migrate to API
    # Add new reports.
    queued_reports = []
    oauth = api.google.auth_session(request, account.oauth_token)
    r = api.google.Query(oauth).get_profiles(account_id=account.id)
    for item in r['items']:
        profile_id = int(item['id'])
        if profile_id not in profile_ids:
            continue

        report = model.Report.create(account_id=account.id)
        report.remote_data = item
        report.display_name = h.human_url(item['websiteUrl']) or item['name']
        model.Subscription.create(user_id=user_id, report=report)

        queued_reports.append(report)
        profile_ids.discard(profile_id)

    model.Session.commit()

    # Queue new reports
    for report in queued_reports:
        tasks.report.send_weekly.delay(report.id)

    if queued_reports:
        request.flash("First report has been queued. Please check your Spam folder if you don't see it in your Inbox in a few minutes.")
    else:
        request.flash('Updated subscription.')


@expose_api('settings.payments')
def settings_payments(request):
    u = api.account.get_user(request, required=True)
    stripe_token, = get_many(request.params, required=['stripe_token'])
    stripe.api_key = request.registry.settings['stripe.private_key']

    description = 'Briefmetrics'

    if u.stripe_customer_id:
        customer = stripe.Customer.retrieve(u.stripe_customer_id)
        customer.card = stripe_token
        customer.description = description
        customer.save()
    else:
        customer = stripe.Customer.create(
            card=stripe_token,
            description=description,
            email=u.auth_email and u.auth_email[0].email,
        )
        u.stripe_customer_id = customer.id
        model.Session.commit()

    if request.params.get('format') == 'redirect':
        request.flash('Payment information is set.')


class SettingsController(Controller):

    @handle_api('settings.subscribe')
    def index(self):
        user_id = api.account.get_user_id(self.request, required=True)
        account = model.Account.get_by(user_id=user_id)
        oauth = api.google.auth_session(self.request, account.oauth_token)

        self.c.report_ids = set(r.remote_data['id'] for r in account.reports)
        self.c.result = api.google.Query(oauth).get_profiles(account_id=account.id)

        return self._render('settings.mako')
