from sqlalchemy import orm

from briefmetrics import api, model, tasks
from briefmetrics.model.meta import Session

from briefmetrics.lib.controller import Controller


class AdminController(Controller):

    DEFAULT_NEXT='/admin'
    title = 'Admin Panel'

    def index(self):
        api.account.get_admin(self.request)
        q = Session.query(model.User)
        q = q.options(orm.joinedload_all('account.reports'))
        q = q.order_by(model.User.id.asc())
        self.c.users = q.all()

        return self._render('admin/index.mako')

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
