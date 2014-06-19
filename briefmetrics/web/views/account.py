from briefmetrics.lib.controller import Controller

from briefmetrics import api, model, tasks
from briefmetrics.lib.exceptions import LoginRequired, APIError, APIControllerError
from briefmetrics.lib.service import registry as service_registry

from unstdlib import get_many

from .api import expose_api


@expose_api('account.login')
def account_login(request):
    is_force, token, save_redirect, service = get_many(request.params, optional=['force', 'token', 'next', 'service'])
    service = service or request.matchdict.get('service', 'google')

    if service != 'google':
        is_force = True

    u = api.account.login_user(request, service=service, save_redirect=save_redirect, token=token, is_force=is_force)

    return {'user': u}


class AccountController(Controller):

    DEFAULT_NEXT = '/reports'

    def login(self):
        account_login(self.request)

        return self._redirect(self.next)

    def connect(self):
        service = self.request.matchdict.get('service', 'google')

        oauth = service_registry[service](self.request)

        try:
            account = api.account.connect_user(self.request, oauth)
        except APIError, e:
            raise APIControllerError(e.message)

        api.account.login_user_id(self.request, account.user_id)

        restored_redirect = self.request.session.pop('next', None)
        self.request.session.save()

        next_url = restored_redirect or self.next or self.request.route_path('reports')

        if not oauth.autocreate_report:
            return self._redirect(next_url)

        try:
            report = api.report.create(account_id=account.id, remote_data=profile, subscribe_user_id=user_id, type=report_type)

            # Queue new report
            tasks.report.send.delay(report.id)

        except APIError as e:
            self.request.session.flash("Failed to create a %s report: %s" % (oauth.autocreate_report.title(), e.message))

        return self._redirect(next_url)

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
