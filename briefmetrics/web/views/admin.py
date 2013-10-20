from sqlalchemy import orm

from briefmetrics import api, model, task
from briefmetrics.model.meta import Session

from briefmetrics.lib.controller import Controller


class AdminController(Controller):

    DEFAULT_NEXT='/admin'
    title = 'Admin Panel'

    def index(self):
        api.account.get_admin(self.request)
        self.c.users = Session.query(model.User).options(orm.joinedload('account')).all()

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

        task.admin.test_errors.delay("This is a test.")

        raise Exception("This is a test.")
