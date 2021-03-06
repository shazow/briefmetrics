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
    remote_id, report_type, account_id, pace = get_many(request.params, optional=['remote_id', 'type', 'account_id', 'pace'])

    user = api.account.get_user(request, required=True, joinedload='accounts')
    user_id = user.id
    account = user.get_account(id=account_id)
    if not account:
        raise APIControllerError("Account [%s] does not exist for user: %s" % (account_id, user_id))

    # Check limits
    num_sites = user.get_feature('num_sites')
    if num_sites:
        remote_ids = set(r.remote_id for r in account.reports)
        remote_ids.add(remote_id)
        if len(remote_ids) > num_sites:
            raise APIControllerError("Maximum number of sites limit reached, please consider upgrading your plan.")

    if not remote_id:
        remote_id = account.remote_id

    api_query = api.account.query_service(request, account=account)
    profile = api_query.get_profile(remote_id=remote_id)
    if not profile:
        raise APIControllerError("Profile does not belong to this account: %s" % remote_id)

    if profile.get('type') == u'APP':
        # TODO: Unhardcode this
        if report_type == 'mobile-week':
            pass
        elif report_type == 'week':
            report_type = 'mobile-week'
        elif report_type == 'activity-month':
            report_type = 'mobile-month'
        else:
            request.flash("This report type is not supported for mobile apps yet. Making a weekly report instead. Please contact support if you need a new report type.")
            api.email.notify_admin(request, "Attempted mobile report: %s" % report_type, str(user))
            report_type = 'mobile-week'

    config = {}
    if pace:
        config['pace'] = pace

    report_type = report_type or api_query.oauth.default_report
    try:
        report = api.report.create(account_id=account.id, remote_data=profile, subscribe_user_id=user_id, type=report_type, remote_id=remote_id, config=config)
    except APIError as e:
        raise APIControllerError(e.message)

    preferred_hour = user.config.get('preferred_hour')
    if preferred_hour is not None:
        api.report.reschedule(report.id, hour=int(preferred_hour))

    # Queue new report
    tasks.report.send.delay(report.id)
    request.flash("First %s report for %s has been queued. Please check your Spam folder if you don't see it in your Inbox in a few minutes." % (report.type, report.display_name))
    return {'report': report}


@expose_api('report.combine')
def report_combine(request):
    report_ids = request.params.getall('report_ids')
    is_replace = request.params.get('replace')
    with_subscribers = request.params.get('with_subscribers')

    if len(report_ids) <= 1:
        raise APIControllerError('Must combine more than one report.')

    user = api.account.get_user(request, required=True, joinedload='accounts')
    if not user.get_feature('combine_reports'):
        raise APIControllerError("Please upgrade your plan to enable combined reports.")

    r = model.Report.get(report_ids[0])
    account = user.get_account(id=r.account_id)
    if not account:
        raise APIControllerError('Report [%s] does not belong to user: %s' % (r.id, user.id))

    subscribe_user_id = None
    if not with_subscribers:
        subscribe_user_id = user.id

    try:
        report = api.report.combine(report_ids, is_replace=is_replace, account_id=account.id, subscribe_user_id=subscribe_user_id)
    except APIError as e:
        raise APIControllerError(e.message)

    # Queue new report
    tasks.report.send.delay(report.id)
    request.flash("Combined %d reports: %s" % (len(report_ids), report.display_name))
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

    if report.account.user_id != user.id:
        raise APIControllerError("Account does not belong to user: %s" % user.id)

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


@expose_api('funnel.create')
def funnel_create(request):
    user_id = api.account.get_user_id(request, required=True)
    from_account_id, to_report_id, ga_tracking_id = get_many(request.params, required=['from_account_id'], optional=['to_report_id', 'ga_tracking_id'])

    from_account = model.Account.get_by(id=from_account_id, user_id=user_id)
    if not from_account:
        raise APIControllerError("Invalid account: %s" % from_account_id)

    to_display_name = ga_tracking_id
    if not ga_tracking_id:
        to_report = model.Session.query(model.Report).join(model.Account).filter(model.Report.id==to_report_id, model.Account.user_id==user_id).first()
        if to_report:
            ga_tracking_id = to_report.remote_data['webPropertyId']
            to_display_name = to_report.display_name

    if not ga_tracking_id:
        raise APIControllerError("Failed to load Google Analytics tracking id from report: %s" % to_report_id)

    ga_funnels = from_account.config.get('ga_funnels') or []
    ga_funnels.append(ga_tracking_id)
    from_account.config['ga_funnels'] = ga_funnels
    model.Session.commit()

    request.flash("Attached events from Stripe (%s) to Google Analytics property (%s) for new transactions." % (from_account.display_name, to_display_name))


@expose_api('funnel.clear')
def funnel_clear(request):
    user_id = api.account.get_user_id(request, required=True)
    account_id, = get_many(request.params, required=['account_id'])

    account = model.Account.get_by(id=account_id, user_id=user_id)
    if not account:
        raise APIControllerError("Invalid account: %s", account_id)

    account.config.pop('ga_funnels', None)
    account.config.changed()
    model.Session.commit()

    request.flash("Cleared event connections from %s account: %s" % (account.service, account.display_name))


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

        available_profiles = []
        google_account = user.get_account(service='google')
        if google_account:
            query = api.account.query_service(self.request, account=google_account)
            try:
                available_profiles += query.get_profiles()
            except APIError as e:
                if e.response:
                    r = e.response.json()
                    for msg in r['error']['errors']:
                        self.request.flash('Error: %s' % msg['message'])
                else:
                    self.request.flash(e.message)

        self.c.available_profiles = available_profiles

        enable_reports = set(user.config.get('enable_reports', []) + list(model.Report.DEFAULT_ENABLED))
        self.c.report_types = [(id, label, id==model.Report.DEFAULT_TYPE) for id, label in model.Report.TYPES if id in enable_reports]

        self.c.google_account = google_account

        self.c.accounts_by_service = {}
        for a in user.accounts:
            self.c.accounts_by_service.setdefault(a.service, []).append(a)

        self.c.user = user
        self.c.reports = []
        for account in user.accounts:
            self.c.reports += account.reports

        self.c.sites = sorted(Site.from_list(self.c.reports), key=lambda s: s.display_name)

        return self._render('reports.mako')


    def view(self):
        user = api.account.get_user(self.request, required=True, joinedload='accounts')
        report_id = self.request.matchdict['id']

        q = model.Session.query(model.Report).filter_by(id=report_id)
        if not user.is_admin:
            q = q.join(model.Report.account).filter_by(user_id=user.id)

        report = q.first()
        if not report:
            raise httpexceptions.HTTPNotFound()

        config_options = ['pace', 'intro', 'ads', 'bcc']
        config = dict((k, v) for k, v in self.request.params.items() if k in config_options and v)

        # Last Sunday
        since_time = now()
        report_context = api.report.fetch(self.request, report, since_time, config=config)

        template = report_context.template
        if not report_context.data:
            template = 'email/error_empty.mako'

        html = api.email.render(self.request, template, Context({
            'report': report_context,
            'user': user,
        }))

        is_send = self.request.params.get('send')
        if is_send:
            owner = report_context.owner
            email_kw = {}
            debug_bcc = config.get('bcc')
            from_name, from_email, reply_to, api_mandrill_key = get_many(owner.config, optional=['from_name', 'from_email', 'reply_to', 'api_mandrill_key'])
            if from_name:
                email_kw['from_name'] = from_name
            if from_email:
                email_kw['from_email'] = from_email
            if reply_to and reply_to != from_email:
                email_kw['reply_to'] = reply_to
            if debug_bcc:
                email_kw['debug_bcc'] = debug_bcc

            send_kw = {}
            if api_mandrill_key:
                send_kw['settings'] = {
                    'api.mandrill.key': api_mandrill_key,
                }

            to_email = user.email
            message = api.email.create_message(self.request,
                to_email=to_email,
                subject=report_context.get_subject(),
                html=html,
                **email_kw
            )
            api.email.send_message(self.request, message, **send_kw)
            self.request.session.flash('Sent report for [%s] to: %s' % (report.display_name, to_email))
            return self._redirect(self.request.route_path('reports'))


        return Response(html)
