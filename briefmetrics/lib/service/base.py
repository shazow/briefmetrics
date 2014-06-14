import time
from requests_oauthlib import OAuth2Session

from briefmetrics.model.meta import Session


registry = {}


class RegistryMeta(type):
    def __init__(cls, name, bases, attrs):
        super(RegistryMeta, cls).__init__(name, bases, attrs)

        id = getattr(cls, 'id', None)
        if not id:
            return

        if id in registry:
            raise KeyError("Service already registered: %s" % name)

        registry[id] = cls


class OAuth2API(object):
    __metaclass__ = RegistryMeta
    config = {}  # Extend and override this.

    def __init__(self, request, token=None, state=None):
        self.request = request

        if token and 'expires_at' in token:
            token['expires_in'] = int(token['expires_at'] - time.time())

        # TODO: Investigate if OAuth2Session reuses connections?
        self.session = OAuth2Session(
            self.config['client_id'],
            redirect_uri=request.route_url('account_connect'),
            scope=self.config['scope'],
            auto_refresh_url=self.config['token_url'],
            auto_refresh_kwargs={
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret'],
            },
            token_updater=_token_updater(token),
            token=token,
            state=state,
        )

    def auth_url(self, is_force=True):
        return self.session.authorization_url(
            self.config['auth_url'],
            access_type='offline',
            approval_prompt='force' if is_force else 'auto',
        )

    def auth_token(self, response_url):
        token = self.session.fetch_token(
            self.config['token_url'],
            authorization_response=response_url,
            client_secret=self.config['client_secret'],
        )
        return _clean_token(token)


def _token_updater(old_token):
    def wrapped(new_token):
        token = _clean_token(new_token)

        old_token.update(token)
        Session.commit()

    return wrapped


def _clean_token(token):
    return {
        'access_token': token['access_token'],
        'token_type': token['token_type'],
        'refresh_token': token['refresh_token'],
        'expires_at': int(time.time() + token['expires_in']),
    }
