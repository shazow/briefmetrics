from .base import Controller

from briefmetrics import api

class AccountController(Controller):

    def login(self):
        # TODO: Use `next` for state?
        oauth = api.google.auth_session(self.request)
        next, state = api.google.auth_url(oauth)
        self.session['oauth_state'] = state

        return self._redirect(location=next)

    def connect(self):
        oauth = api.google.auth_session(self.request, state=self.session.get('oauth_state'))

        url = self.request.current_route_url().replace('http://', 'https://') # We lie, because honeybadger.
        token = api.google.auth_token(oauth, url)

        # Identify user
        r = oauth.get('https://www.googleapis.com/oauth2/v1/userinfo')
        r.raise_for_status()

        user_info = r.json(indent=4)
        user = api.account.get_or_create(
            email=user_info['email'],
            token=token,
            display_name=user_info['name'],
        )
        api.account.login_user_id(self.request, user.id)

        return self._redirect(location=self.next)

    def logout(self):
        api.account.logout_user(self.request)
        return self._redirect(location=self.next or '/')
