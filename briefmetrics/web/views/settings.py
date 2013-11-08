from unstdlib import get_many

from briefmetrics import api
from briefmetrics.lib.exceptions import APIError

from .api import expose_api, handle_api
from briefmetrics.lib.controller import Controller


@expose_api('settings.payments')
def settings_payments(request):
    user = api.account.get_user(request, required=True)
    stripe_token, = get_many(request.params, required=['stripe_token'])

    api.account.set_payments(user, stripe_token)

    api.email.notify_admin(request, 'Payment added: [%s] %s' % (user.id, user.display_name))

    request.flash('Payment information is set.')


@expose_api('settings.payments_cancel')
def settings_payments_cancel(request):
    user = api.account.get_user(request, required=True)
    api.account.delete_payments(user)

    api.email.notify_admin(request, 'Payment removed: [%s] %s' % (user.id, user.display_name))

    request.flash('Subscription cancelled.')


class SettingsController(Controller):

    @handle_api(['settings.subscribe', 'settings.payments_cancel'])
    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload=['account'])
        account = user.account
        oauth = api.google.auth_session(self.request, account.oauth_token)

        try:
            self.c.result = api.google.Query(oauth).get_profiles(account_id=account.id)
        except APIError as e:
            r = e.response.json()
            for msg in r['error']['errors']:
                self.request.flash('Error: %s' % msg['message'])

            self.c.result = []

        self.c.user = user
        self.c.report_ids = set((r.remote_id or r.remote_data.get('id')) for r in account.reports)

        return self._render('settings.mako')
