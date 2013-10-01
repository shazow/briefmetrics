from sqlalchemy import orm

from briefmetrics import api
from briefmetrics import model
from briefmetrics.model.meta import Session

from .base import Controller


class AdminController(Controller):

    DEFAULT_NEXT='/admin'
    title = 'Admin Panel'

    def index(self):
        u = api.account.get_user(self.request, required=True)
        assert u.is_admin

        self.c.users = Session.query(model.User).options(orm.joinedload('account')).all()

        return self._render('admin/index.mako')

