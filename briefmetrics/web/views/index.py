import os

from briefmetrics import api
from briefmetrics.lib.controller import Controller
from briefmetrics.web.environment import httpexceptions

from mako.exceptions import TopLevelLookupException


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

    def articles(self):
        template_name = os.path.basename(self.request.matchdict['id'])
        try:
            return self._render('articles/{}.mako'.format(template_name))
        except TopLevelLookupException:
            raise httpexceptions.HTTPNotFound('Article does not exist: {}'.format(template_name))
