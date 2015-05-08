from sqlalchemy import orm
from unstdlib import get_many, groupby_count, now
from datetime import date, timedelta

from briefmetrics.web.environment import Response
from briefmetrics import api, model, tasks
from briefmetrics.model.meta import Session
from briefmetrics.lib.controller import Controller
from briefmetrics.lib.exceptions import APIControllerError
from briefmetrics.lib.table import Column

from .api import expose_api


@expose_api('admin.dry_run')
def dry_run(request):
    api.account.get_admin(request)
    num_extra = int(request.params.get('num_extra', 10))
    tasks.report.dry_run.delay(num_extra=num_extra)
    request.flash('Dry run queued.')


@expose_api('admin.explore_api')
def explore_api(request):
    u = api.account.get_admin(request)
    a = u.get_account(service='google')

    report_id, dimensions, metrics, extra, date_start, date_end = get_many(request.params, ['report_id'], optional=['dimensions', 'metrics', 'extra', 'date_start', 'date_end'])
    report = model.Report.get_by(account_id=a.id, id=report_id)

    if not report:
        raise APIControllerError("Invalid report id: %s" % report_id)

    cache_keys = ('admin/explore_api',)
    google_oauth2 = api.google.OAuth2(request, token=a.oauth_token)
    google_query = api.google.create_query(request, google_oauth2.session, cache_keys=cache_keys)

    date_end = date_end or date.today()
    date_start = date_start or date_end - timedelta(days=7)

    params = {
        'ids': 'ga:%s' % report.remote_id,
        'start-date': date_start,
        'end-date': date_end,
    }

    if metrics:
        metrics = [Column(m) for m in metrics.split(',')]

    if dimensions:
        dimensions = [Column(m) for m in dimensions.split(',')]

    if extra:
        params.update(part.split('=', 1) for part in extra.split('&'))


    try:
        r = google_query.get_table(params, metrics=metrics, dimensions=dimensions)
    except KeyError as e:
        raise APIControllerError("Invalid metric or dimension: %s" % e.args[0])

    return {'table': r}


class AdminController(Controller):

    DEFAULT_NEXT='/admin'
    title = 'Admin Panel'
    track_analytics = False

    def index(self):
        api.account.get_admin(self.request)
        q = Session.query(model.User)
        q = q.options(orm.joinedload_all('accounts.reports'), orm.joinedload_all('subscriptions'))
        q = q.order_by(model.User.id.asc())
        users = q.all()

        self.c.active_users, self.c.inactive_users, self.c.active_trials = [], [], []
        for u in users:
            account_reports = [a.reports for a in u.accounts]
            if u.is_active and (u.subscriptions or account_reports or u.payment):
                self.c.active_users.append(u)
                if u.plan_id == 'trial':
                    self.c.active_trials.append(u)
            else:
                self.c.inactive_users.append(u)

        credit_cards = [u for u in users if u.payment and u.payment.is_charging and u.num_remaining is None]
        self.c.num_users = len(users)
        self.c.num_credit_cards = len(credit_cards)
        self.c.num_mrr = sum((u.plan.price_monthly or 0) for u in credit_cards)

        self.c.by_plan = groupby_count(users, key=lambda u: u.plan_id)

        self.c.expiring_trials = []
        for u in self.c.active_trials:
            num_reports = len([a.reports for a in u.accounts])
            if num_reports * 2 < u.num_remaining:
                continue
            self.c.expiring_trials.append(u)

        q = Session.query(model.ReportLog).order_by(model.ReportLog.id.desc()).limit(10)
        self.c.recent_reports = q.all()

        return self._render('admin/index.mako')

    def user(self):
        u = api.account.get_admin(self.request)

        user_id = self.request.matchdict['id']
        q = Session.query(model.User)
        q = q.options(orm.joinedload_all('accounts.reports.subscriptions.user'))
        self.c.user = q.get(user_id)

        q = Session.query(model.User).filter_by(invited_by_user_id=user_id)
        q = q.options(orm.joinedload_all('subscriptions'))
        self.c.invited = q.all()

        self.c.invited_by = None
        if self.c.user.invited_by_user_id:
            self.c.invited_by = model.User.get(self.c.user.invited_by_user_id)

        q = Session.query(model.ReportLog).join(model.Account).filter_by(user_id=self.c.user.id) # XXX: accounts
        q = q.order_by(model.ReportLog.id.desc()).limit(10)
        self.c.recent_reports = q.all()

        return self._render('admin/user.mako')


    def explore_api(self):
        u = api.account.get_admin(self.request)
        self.c.reports = u.reports
        self.c.user = u

        self.c.date_end = date.today()
        self.c.date_start = self.c.date_end - timedelta(days=7)

        return self._render('admin/explore_api.mako')

    def report_log(self):
        api.account.get_admin(self.request)
        report_log_id = self.request.matchdict['id']

        report_log = model.ReportLog.get(report_log_id)
        return Response(report_log.body)

    def login_as(self):
        u = api.account.get_admin(self.request)

        user_id = int(self.request.params.get('id'))

        self.session['user_id'] = user_id
        self.session['admin_id'] = u.id
        self.session.save()

        return self._redirect(self.request.route_path('index'))

    def test_errors(self):
        api.account.get_admin(self.request)

        tasks.admin.test_errors.delay("This is a test.")

        raise Exception("This is a test.")

    def health(self):
        errors = []

        cutoff = now() - timedelta(hours=1)
        report = api.report.get_pending(since_time=cutoff, max_num=1, include_new=False).first()
        if report:
            errors.append('Report delivery lagged by {}: {}'.format(
                now() - report.time_next, report))

        if errors:
            raise Exception('\n'.join(errors))

        return Response(':)')
