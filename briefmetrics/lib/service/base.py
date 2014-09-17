from requests_oauthlib import OAuth2Session

from briefmetrics.lib.registry import registry_metaclass
from briefmetrics.model.meta import Session

registry = {}


class OAuth2API(object):
    __metaclass__ = registry_metaclass(registry)
    config = {}  # Extend and override this.

    id = None
    label = 'ACME Api'
    description = ''

    default_report = None
    is_autocreate = False

    def __init__(self, request, token=None, state=None):
        self.request = request

        # TODO: Investigate if OAuth2Session reuses connections?
        self.session = OAuth2Session(
            self.config['client_id'],
            redirect_uri=request.route_url('account_connect', service=self.id),
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
        return token


def _token_updater(old_token):
    def wrapped(new_token):
        old_token.update(new_token)
        Session.commit()

    return wrapped
