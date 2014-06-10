import datetime
from itertools import groupby
from unstdlib import now, get_many
from sqlalchemy import orm

from briefmetrics import api, model, tasks
from briefmetrics.web.environment import Response, httpexceptions
from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.exceptions import APIControllerError, APIError

from .api import expose_api, handle_api


@expose_api('report.create')
def report_create(request):
    report_id, report_type, account_id = get_many(request.params, required=['report_id'], optional=['report_type', 'account_id'])
    report_type = report_type or 'week'
    if not remote_id:
        raise APIControllerError("Select a report to create.")

    user = api.account.get_user(request, required=True, joinedload='accounts')
    user_id = user.id
    account = user.account # XXX: accounts
    if not account:
        raise APIControllerError("Account does not exist for user: %s" % user_id)

    # Check limits
    num_sites = user.get_feature('num_sites')
    if num_sites:
        remote_ids = set(r.remote_id for r in account.reports)
        remote_ids.add(remote_id)
        if len(remote_ids) > num_sites:
            raise APIControllerError("Maximum number of sites limit reached, please consider upgrading your plan.")

    google_session = api.google.GoogleAPI(request, token=account.oauth_token)
    google_query = api.google.create_query(request, google_session.session)
    r = google_query.get_profiles(account_id=account.id)

    # Find profile item
    profile = next((item for item in r['items'] if item['id'] == remote_id), None)
    if not profile:
        raise APIControllerError("Profile does not belong to this account: %s" % remote_id)

    try:
        report = api.report.create(account_id=account.id, remote_data=profile, subscribe_user_id=user_id, type=report_type)
    except APIError as e:
        raise APIControllerError(e.message)

    # Queue new report
    tasks.report.send.delay(report.id)

    request.flash("First %s report for %s has been queued. Please check your Spam folder if you don't see it in your Inbox in a few minutes." % (report.type, report.display_name))

    return {'report': report}


@expose_api('report.delete')
def report_delete(request):
    report_id = request.params['report_id']
    user_id = api.account.get_user_id(request, required=True)

    report = model.Report.get(report_id)
    if not report:
        raise APIControllerError("Invalid report id: %s" % report_id)

    if report.account.user_id != user_id:
        raise APIControllerError("Account does not belong to user: %s" % user_id)

    display_name = report.display_name
    model.Session.delete(report)
    model.Session.commit()
    request.flash("Report removed: %s" % display_name) 


@expose_api('subscription.create')
def subscription_create(request):
    report_id, email, display_name = get_many(request.params, required=['report_id', 'email'], optional=['display_name'])

    if '@' not in email:
        raise APIControllerError('Invalid email address: %s' % email)

    user = api.account.get_user(request, required=True)

    report = model.Report.get(report_id)
    if not report:
        raise APIControllerError("Invalid report id: %s" % report_id)

    if report.account.user_id != user_id:
        raise APIControllerError("Account does not belong to user: %s" % user_id)

    num_recipients = user.get_feature('num_recipients')
    if num_recipients and len(report.subscriptions) >= num_recipients:
        raise APIControllerError("Maximum number of recipients limit reached, please consider upgrading your plan.")

    new_user = api.report.add_subscriber(report_id, email, display_name, invited_by_user_id=user.id)

    request.flash("Added subscriber [%s] to report for [%s]" % (new_user.email, report.display_name))

    return {'user': new_user}


@expose_api('subscription.delete')
def subscription_delete(request):
    # TODO: Remove report if it's the last subscriber?
    user_id = api.account.get_user_id(request, required=True)
    subscription_id, = get_many(request.params, required=['subscription_id'])

    sub = model.Session.query(model.Subscription).options(orm.joinedload_all('report.account'), orm.joinedload('user')).get(subscription_id)
    if not sub:
        raise APIControllerError("Invalid subscription id: %s" % subscription_id)

    report = sub.report
    if sub.user_id != user_id and report.account.user_id != user_id:
        raise APIControllerError("Subscription does not belong to you: %s" % subscription_id)

    email = sub.user.email
    sub.delete()
    model.Session.commit()

    request.flash("Removed subscriber [%s] to report for [%s]" % (email, report.display_name))


# TODO: Move this somewhere else?
class Site(object):
    report_types = model.Report.TYPES

    def __init__(self, reports, remote_id=None, display_name=None):
        self.reports_by_type = {}
        for report in reports:
            self.reports_by_type[report.type] = report

        self.display_name = display_name or report.display_name
        self.remote_id = remote_id or report.remote_id
        self.report = report

    @classmethod
    def from_list(cls, reports):
        sorted_reports = sorted(reports, key=lambda r: r.remote_id)
        for _, reports in groupby(sorted_reports, key=lambda r: r.remote_id):
            yield cls(reports)

    def __iter__(self):
        for t, _ in self.report_types:
            report = self.reports_by_type.get(t)
            if not report:
                continue

            yield t, report


class ReportController(Controller):

    @handle_api(['report.create', 'report.delete'])
    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='accounts.reports.subscriptions.user')

        google_session = api.google.GoogleAPI(self.request, token=user.account.oauth_token)
        q = api.google.create_query(self.request, google_session.session)
        try:
            self.c.available_profiles = q.get_profiles(account_id=user.account.id)
        except APIError as e:
            r = e.response.json()
            for msg in r['error']['errors']:
                self.request.flash('Error: %s' % msg['message'])

            self.c.available_profiles = []

        enable_reports = set(user.config.get('enable_reports', []) + [model.Report.DEFAULT_TYPE])
        self.c.report_types = [(id, label, id==model.Report.DEFAULT_TYPE) for id, label in model.Report.TYPES if id in enable_reports]

        self.c.user = user
        self.c.reports = user.account.reports # XXX: accounts
        self.c.sites = sorted(Site.from_list(self.c.reports), key=lambda s: s.display_name)

        return self._render('reports.mako')


    def view(self):
        user = api.account.get_user(self.request, required=True, joinedload='accounts')
        report_id = self.request.matchdict['id']

        q = model.Session.query(model.Report).filter_by(id=report_id)
        if not user.is_admin:
            q = q.filter_by(account_id=user.account.id) # XXX: accounts

        report = q.first()
        if not report:
            raise httpexceptions.HTTPNotFound()

        # Last Sunday
        since_time = now()
        report_context = api.report.fetch(self.request, report, since_time)

        template = report_context.template
        if not report_context.data:
            template = 'email/error_empty.mako'

        html = api.report.render(self.request, template, Context({
            'report': report_context,
            'user': user,
        }))

        if self.request.params.get('send'):
            owner = report_context.owner
            email_kw = {}
            from_name, reply_to = get_many(owner.config, optional=['from_name', 'reply_to'])
            if from_name:
                email_kw['from_name'] = from_name
            if reply_to:
                email_kw['reply_to'] = reply_to

            message = api.email.create_message(self.request,
                to_email=user.email,
                subject=report_context.get_subject(), 
                html=html,
                **email_kw
            )
            api.email.send_message(self.request, message)

        return Response(html)
