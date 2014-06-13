from briefmetrics.lib.controller import Controller

from briefmetrics import api, model
from briefmetrics.lib.exceptions import LoginRequired
from briefmetrics.lib.exceptions import APIControllerError, APIError

from .api import expose_api


@expose_api('account.login')
def account_login(request):
    try:
        u = api.account.login_user(request)
    except APIError:
        raise APIControllerError('Invalid login.')

    return {'user': u}


class AccountController(Controller):

    DEFAULT_NEXT = '/reports'

    def login(self):
        account_login(self.request)

        return self._redirect(self.next)

    def connect(self):
        user = api.google.connect_user(self.request)
        api.account.login_user_id(self.request, user.id)

        restored_redirect = self.request.session.pop('next', None)
        self.request.session.save()

        return self._redirect(restored_redirect or self.next or self.request.route_path('reports'))

    def logout(self):
        api.account.logout_user(self.request)
        return self._redirect(location='/')

    def delete(self):
        # TODO: Move to API?
        user_id = api.account.get_user_id(self.request)
        token = self.request.params.get('token')

        if not user_id and not token:
            raise LoginRequired(next=self.current_path)

        user = None
        if token:
            user = api.account.get(token=token)

        if not user and user_id:
            user = model.User.get(user_id)

        self.c.user = user
        self.c.token = token

        if not user:
            return self._render('delete.mako')

        confirmed = self.request.params.get('confirmed')
        if not confirmed:
            self.c.token = token
            return self._render('delete.mako')

        api.email.notify_admin(self.request, 'Account deleted: [%s] "%s" <%s>' % (user.id, user.display_name, user.email))
        api.account.delete(user_id=user.id)
        self.request.session.flash('Good bye.')

        return self._redirect(location=self.request.route_path('index'))
