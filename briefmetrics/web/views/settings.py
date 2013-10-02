import re
from unstdlib import get_many

from briefmetrics import api, model
from briefmetrics.lib.exceptions import APIControllerError

from .api import expose_api
from .base import Controller


RE_HUMAN_URL = re.compile('^(\w*://)?(www\.)?(.+)/?$')


@expose_api('settings.subscribe')
def settings_subscribe(request):
    # TODO: Support multiple
    profile_id, = get_many(request.params, ['profile_id'])
    user_id = api.account.get_user_id(request, required=True)

    account = model.Account.get_by(user_id=user_id)
    if not account:
        raise APIControllerError("Account does not exist for user: %s" % user_id)

    report = model.Report.get_or_create(account_id=account.id)
    if report.remote_data and report.remote_data['id'] == profile_id:
        request.flash('Already subscribed to %s' % report.display_name)
        return {'report': report}

    profiles = api.google.get_profile(request, account)

    p = next((item for item in profiles['items'] if item['id'] == profile_id), None)
    if not p:
        request.flash('Invalid profile id: %s' % profile_id)
        return {}

    report.remote_data = p
    report.display_name = RE_HUMAN_URL.match(p['websiteUrl']).group(3)
    model.Subscription.get_or_create(user_id=user_id, report=report)
    model.Session.commit()

    request.flash('Changed subscription to %s' % report.display_name)

    return {'report': report}


class SettingsController(Controller):

    def index(self):
        user_id = api.account.get_user_id(self.request, required=True)
        self.c.result = api.google.get_profile(self.request, user_id)

        return self._render('report.mako')
