from briefmetrics.web import views
from contextlib import contextmanager


@contextmanager
def handler_routes(config, handler):
    "Helper for adding a bulk of routes per handler."
    def _wrapper(route_name, pattern, action=None, **kw):
        config.add_handler(route_name, pattern, handler=handler, action=action, **kw)
    yield _wrapper


def add_routes(config):
    config.add_route('api', '/api', views.api.index)

    with handler_routes(config, views.index.IndexController) as route:
        route('index', '/', action='index')

    return config
