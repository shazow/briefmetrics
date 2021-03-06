from briefmetrics.lib.controller import Controller

from briefmetrics import api, model
from briefmetrics.lib.exceptions import LoginRequired, APIError, APIControllerError
from briefmetrics.lib.service import registry as service_registry

import jwt
from urllib.parse import parse_qs
from unstdlib import get_many

from .api import expose_api


@expose_api('account.login', check_csrf=False, check_referer=False)
def account_login(request):
    is_force, token, save_redirect, service = get_many(request.params, optional=['force', 'token', 'next', 'service'])
    service = service or request.matchdict.get('service', 'google')

    if service == 'stripe':
        # We don't do native auth with Stripe.
        if not api.account.get_user_id(request):
            # Not logged in? Force Google first.
            save_redirect  = request.route_url('account_login', service=service, _query={'next': save_redirect})
            service = 'google'
        else:
            is_force = True

    u = api.account.login_user(request, service=service, save_redirect=save_redirect, token=token, is_force=is_force)

    return {'user': u}


@expose_api('account.connect')
def account_connect(request):
    # TODO: Move /account/*/connect logic in here too?
    payload, service_id = get_many(request.params, ["payload", "service"])
    service = service_registry[service_id]

    if service.protocol != 'openidconnect':
        raise APIControllerError('OpenID Connect not supported for service.')

    p = parse_qs(payload)
    id_token, = p['id_token']
    decode_options = {}
    if request.registry.settings.get('testing'):
        decode_options = {
           'verify_exp': False,
        }

    try:
        decoded = jwt.decode(id_token, service.config['sso_client_secret'], audience=service.config['sso_client_id'], options=decode_options)
    except jwt.DecodeError as e:
        raise APIControllerError('Failed to verify id token: %s' % e)
    except (jwt.InvalidTokenError, jwt.InvalidIssuedAtError) as e:
        raise APIControllerError('Invalid token: %s' % e)

    remote_id = decoded['sub']
    account = model.Session.query(model.Account).filter_by(remote_id=remote_id, service=service_id).first()
    if not account:
        # TODO: Create on demand?
        raise APIControllerError('Account does not exist.')

    api.account.login_user_id(request, account.user_id)

    redirect_to = '/reports'
    return {'redirect': redirect_to, 'decoded': decoded}


class AccountController(Controller):

    DEFAULT_NEXT = '/reports'

    def login(self):
        account_login(self.request)

        return self._redirect(self.next)

    def connect(self):
        service = self.request.matchdict.get('service', 'google')
        oauth = service_registry[service](self.request)

        if oauth.protocol == 'openidconnect':
            self.c.service = oauth.id
            return self._render('openidconnect.mako')

        try:
            account = api.account.connect_oauth(self.request, oauth)
        except APIError as e:
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

    def disconnect(self):
        user = api.account.get_user(self.request, required=True, joinedload='accounts')
        account_id, = get_many(self.request.params, ['account_id'])

        account = user.get_account(id=account_id)
        if not account:
            raise APIControllerError('Invalid account id: %s' % account_id)

        if len(user.accounts) == 1:
            raise APIControllerError('Cannot disconnect last remaining service while retaining the account.')

        # TODO: Stop doing model stuff
        display_name = account.display_name
        model.Session.delete(account)
        model.Session.commit()

        self.request.flash('Account disconnected: %s' % display_name)

        return self._redirect(location='/settings')


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
