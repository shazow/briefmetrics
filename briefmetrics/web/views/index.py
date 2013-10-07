from briefmetrics import api

from briefmetrics.lib.controller import Controller


class IndexController(Controller):
    def index(self):
        self.c.user = api.account.get_user(self.request)

        return self._render('index.mako')
