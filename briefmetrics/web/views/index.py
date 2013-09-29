from .base import Controller


class IndexController(Controller):
    def index(self):
        return "Hello, world."
