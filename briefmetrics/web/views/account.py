from .base import Controller

from briefmetrics import api, model
from briefmetrics.lib.exceptions import LoginRequired

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

    def unsubscribe(self):
        # TODO: Move to API?
        user_id = api.account.get_user_id(self.request)
        token = self.request.params.get('token')

        if not user_id and not token:
            raise LoginRequired(next=self.current_path)

        id, email_token = token.split('-', 2)
        user = model.User.get_by(id=id, email_token=email_token)
        if not user:
            self.request.flash('Invalid token. Try signing in to unsubscribe?')
            return self._render('unsubscribe.mako')

        confirmed = self.request.params.get('confirmed')
        if not confirmed:
            self.c.token = token
            return self._render('unsubscribe.mako')

        user.delete()
        model.Session.commit()
        self.request.flash('Good bye.')

        return self._redirect(location=self.request.route_path('index'))
