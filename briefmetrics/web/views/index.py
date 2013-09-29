from .base import Controller


class IndexController(Controller):
    def index(self):
        return self._render('index.mako')
