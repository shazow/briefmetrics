from .base import Controller

from briefmetrics import api

class AccountController(Controller):

    def login(self):
        oauth = api.google.auth_session(self.request)
        next, state = api.google.auth_url(oauth)
        self.session['oauth_state'] = state
        print "Redirecting to", next
        return self._redirect(location=next)

    def connect(self):
        oauth = api.google.auth_session(self.request, state=self.session.get('oauth_state'))

        url = self.request.current_route_url().replace('http://', 'https://') # We lie, because honeybadger.
        token = api.google.auth_token(oauth, url)
        print "Got token", token
        # TODO: Save token
        return self._redirect(location=self.next)
