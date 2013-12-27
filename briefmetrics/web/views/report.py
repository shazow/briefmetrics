import datetime
from unstdlib import now

from briefmetrics import api, model, tasks
from briefmetrics.web.environment import Response, httpexceptions
from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.exceptions import APIControllerError, APIError

from .api import expose_api, handle_api


@expose_api('report.create')
def report_create(request):
    remote_id = request.params['remote_id']
    if not remote_id:
        raise APIControllerError("Select a report to create.")

    user_id = api.account.get_user_id(request, required=True, )

    account = model.Account.get_by(user_id=user_id)
    if not account:
        raise APIControllerError("Account does not exist for user: %s" % user_id)

    oauth = api.google.auth_session(request, account.oauth_token)
    q = api.google.create_query(request, oauth)
    r = q.get_profiles(account_id=account.id)

    # Find profile item
    profile = next((item for item in r['items'] if item['id'] == remote_id), None)
    if not profile:
        raise APIControllerError("Profile does not belong to this account: %s" % remote_id)

    try:
        report = api.report.create(account_id=account.id, remote_data=profile, subscribe_user_id=user_id)
    except APIError as e:
        raise APIControllerError(e.message)

    # Queue new report
    tasks.report.send.delay(report.id)

    request.flash("First report for %s has been queued. Please check your Spam folder if you don't see it in your Inbox in a few minutes." % report.display_name)

    return {'report': report}


@expose_api('report.update')
def report_update(request):
    report_id = request.params['report_id']
    user_id = api.account.get_user_id(request, required=True)

    account = model.Account.get_by(user_id=user_id)
    if not account:
        raise APIControllerError("Account does not exist for user: %s" % user_id)

    report = model.Report.get_by(account_id=account.id, id=report_id)
    if not report:
        raise APIControllerError("Invalid report id: %s" % report_id)

    if request.params.get('delete'):
        display_name = report.display_name
        model.Session.delete(report)
        model.Session.commit()
        request.flash("Report removed: %s" % display_name) 
        return


class ReportController(Controller):

    @handle_api(['report.create', 'report.update'])
    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account.reports')

        oauth = api.google.auth_session(self.request, user.account.oauth_token)
        q = api.google.create_query(self.request, oauth)
        try:
            self.c.available_profiles = q.get_profiles(account_id=user.account.id)
        except APIError as e:
            r = e.response.json()
            for msg in r['error']['errors']:
                self.request.flash('Error: %s' % msg['message'])

            self.c.available_profiles = []

        self.c.user = user
        self.c.reports = user.account.reports

        return self._render('reports.mako')


    def view(self):
        user = api.account.get_user(self.request, required=True, joinedload='account')
        report_id = self.request.matchdict['id']

        q = model.Session.query(model.Report).filter_by(id=report_id)
        if not user.is_admin:
            q = q.filter_by(account_id=user.account.id)

        report = q.first()
        if not report:
            raise httpexceptions.HTTPNotFound()

        # Last Sunday
        since_time = now()
        report_context = api.report.fetch(self.request, report, since_time)

        html = api.report.render(self.request, report_context.template, Context({
            'report': report_context,
            'user': user,
        }))

        if self.request.params.get('send'):
            message = api.email.create_message(self.request,
                to_email=user.email,
                subject=report_context.get_subject(), 
                html=html,
            )
            api.email.send_message(self.request, message)

        return Response(html)
