import re
from unstdlib import get_many

from briefmetrics import api, model
from briefmetrics.lib.exceptions import APIControllerError
from briefmetrics.lib import helpers as h

from .api import expose_api, handle_api
from .base import Controller


@expose_api('settings.subscribe')
def settings_subscribe(request):
    # TODO: Support multiple
    profile_ids = set(map(int, request.params.getall('id')))
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

    # Add new reports.
    r = api.google.get_profiles(request, account)
    for item in r['items']:
        if int(item['id']) not in profile_ids:
            continue

        report = model.Report.create(account_id=account.id)
        report.remote_data = item
        report.display_name = h.human_url(item['websiteUrl']) or item['name']
        model.Subscription.create(user_id=user_id, report=report)

        profile_ids.discard(report.id)

    model.Session.commit()

    request.flash('Updated subscription.')


class SettingsController(Controller):

    @handle_api('settings.subscribe')
    def index(self):
        user_id = api.account.get_user_id(self.request, required=True)
        account = model.Account.get_by(user_id=user_id)
        self.c.report_ids = set(r.remote_data['id'] for r in account.reports)
        self.c.result = api.google.get_profiles(self.request, account)

        return self._render('settings.mako')
