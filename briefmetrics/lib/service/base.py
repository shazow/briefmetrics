from requests_oauthlib import OAuth2Session

from briefmetrics.lib.registry import registry_metaclass

registry = {}


class Service(object, metaclass=registry_metaclass(registry)):
    config = {}  # Extend and override this.

    id = None
    label = 'ACME Api'
    description = ''
    protocol = ''

    default_report = None
    is_autocreate = False


class OAuth2API(Service):
    protocol = 'oauth2'

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
            token_updater=_token_updater(token, request.db),
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


def _token_updater(old_token, db):
    def wrapped(new_token):
        old_token.update(new_token)
        db.commit()

    return wrapped
