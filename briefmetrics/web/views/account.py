from briefmetrics.lib.controller import Controller

from briefmetrics import api, model
from briefmetrics.lib.exceptions import LoginRequired, APIError, APIControllerError
from briefmetrics.lib.service import registry as service_registry

from unstdlib import get_many

from .api import expose_api


@expose_api('account.login', check_csrf=False, check_referer=False)
def account_login(request):
    is_force, token, save_redirect, service = get_many(request.params, optional=['force', 'token', 'next', 'service'])
    service = service or request.matchdict.get('service', 'google')

    if service != 'google':
        if not api.account.get_user_id(request):
            # Not logged in? Force Google first.
            save_redirect  = request.route_url('account_login', service=service, _query={'next': save_redirect})
            service = 'google'
        else:
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

        # TODO: Handle InvalidRequestError?

        api.account.login_user_id(self.request, account.user_id)

        restored_redirect = self.request.session.pop('next', None)
        self.request.session.save()

        next_url = restored_redirect or self.next or self.request.route_path('reports')
        if oauth.is_autocreate:
            next_url = self.request.route_path('api', _query={
                'method': 'report.create',
                'account_id': account.id,
                'format': 'redirect',
                'next': next_url,
                'csrf_token': self.request.session.get_csrf_token(),
            })

        return self._redirect(next_url)

    def logout(self):
        api.account.logout_user(self.request)
        return self._redirect(location='/')

    def delete(self):
        # TODO: Move to API?
        user_id = api.account.get_user_id(self.request)
        token, is_confirmed, is_feedback, why, retention = get_many(self.request.params, optional=['token', 'confirmed', 'feedback', 'why', 'retention'])

        if not user_id and not token:
            raise LoginRequired(next=self.current_path)

        user = None
        if token:
            user = api.account.get(token=token)

        if not user and user_id:
            user = model.User.get(user_id)

        self.c.user = user
        self.c.token = token

        reasons = 'Why:\r\n%s\r\n\r\nRetention:\r\n%s' % (why, retention)

        if not user:
            return self._render('delete.mako')

        if is_confirmed:
            api.email.notify_admin(self.request, 'Account deleted: [%s] "%s" <%s>' % (user.id, user.display_name, user.email), text=reasons)
            api.account.delete(user_id=user.id)
            api.account.logout_user(self.request)
            self.request.session.flash('Good bye.')
        elif is_feedback:
            api.email.notify_admin(self.request, 'RETENTION: [%s] "%s" <%s>' % (user.id, user.display_name, user.email), text=reasons)
            self.request.session.flash('Feedback submitted. We\'ll be in touch shortly!')
        else:
            self.c.token = token
            return self._render('delete.mako')

        return self._redirect(location=self.request.route_path('index'))
