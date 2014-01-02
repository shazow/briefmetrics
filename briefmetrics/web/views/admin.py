from sqlalchemy import orm
from unstdlib import get_many

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

    report_id, dimensions, metrics, extra = get_many(request.params, ['report_id'], optional=['dimensions', 'metrics', 'extra'])
    report = model.Report.get_by(account_id=u.account.id, id=report_id)

    if not report:
        raise APIControllerError("Invalid report id: %s" % report_id)

    oauth = api.google.auth_session(request, u.account.oauth_token)
    google_query = api.google.create_query(request, oauth)
    params = {
        'ids': 'ga:%s' % report.remote_id,
        #'start-date': date_start,
        #'end-date': date_end,
    }

    if metrics:
        metrics = [Column(m) for m in metrics.split(',')]

    if dimensions:
        dimensions = [Column(m) for m in dimensions.split(',')]

    if extra:
        params.update(part.split('=', 1) for part in extra.split('&'))

    cache_keys = ('admin/explore_api',)

    try:
        r = google_query.get_table(params, metrics=metrics, dimensions=dimensions, _cache_keys=cache_keys)
    except KeyError as e:
        raise APIControllerError("Invalid metric or dimension: %s" % e.args[0])

    return {'table': r}


class AdminController(Controller):

    DEFAULT_NEXT='/admin'
    title = 'Admin Panel'

    def index(self):
        api.account.get_admin(self.request)
        q = Session.query(model.User)
        q = q.options(orm.joinedload_all('account.reports'))
        q = q.order_by(model.User.id.asc())
        self.c.users = q.all()

        q = Session.query(model.ReportLog).order_by(model.ReportLog.id.desc()).limit(10)
        self.c.recent_reports = q.all()

        return self._render('admin/index.mako')

    def explore_api(self):
        u = api.account.get_admin(self.request)
        self.c.reports = u.reports
        self.c.user = u

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
