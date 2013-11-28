from briefmetrics import api

from briefmetrics.lib.controller import Controller


class IndexController(Controller):
    def index(self):
        user_id = api.account.get_user_id(self.request)

        if user_id:
            return self._redirect(self.request.route_path('reports'))

        return self._render('index.mako')

    def privacy(self):
        self.title = "Privacy Policy"
        return self._render('privacy.mako')

    def security(self):
        self.title = "Security"
        return self._render('security.mako')
