from briefmetrics import api

from briefmetrics.lib.controller import Controller


class IndexController(Controller):
    def index(self):
        self.c.user = api.account.get_user(self.request)

        return self._render('index.mako')

    def privacy(self):
        self.title = "Privacy Policy"
        return self._render('privacy.mako')

    def security(self):
        self.title = "Security"
        return self._render('security.mako')
