from briefmetrics.web import views
from contextlib import contextmanager


@contextmanager
def handler_routes(config, handler):
    "Helper for adding a bulk of routes per handler."
    def _wrapper(route_name, pattern, action=None, **kw):
        config.add_handler(route_name, pattern, handler=handler, action=action, **kw)
    yield _wrapper


def add_routes(config):
    # Damn you Pyramid for making this two lines.
    config.add_route('api', '/api')
    config.add_view(views.api.index, route_name='api')

    with handler_routes(config, views.index.IndexController) as route:
        route('index', '/', action='index')
        route('pricing', '/pricing', action='pricing')
        route('privacy', '/privacy', action='privacy')
        route('terms', '/terms', action='terms')
        route('security', '/security', action='security')
        route('articles', '/articles/{id}', action='articles')
        route('features', '/features/{id}', action='features')

    with handler_routes(config, views.account.AccountController) as route:
        route('account_login', '/account/login', action='login')
        route('account_logout', '/account/logout', action='logout')
        route('account_connect', '/account/connect', action='connect')
        route('account_delete', '/account/delete', action='delete')

    with handler_routes(config, views.admin.AdminController) as route:
        route('admin', '/admin', action='index')
        route('admin_user', '/admin/user/{id}', action='user')
        route('admin_report_log', '/admin/report_log/{id}', action='report_log')
        route('admin_explore_api', '/admin/explore_api', action='explore_api')
        route('admin_login_as', '/admin/login_as', action='login_as')
        route('admin_test_errors', '/admin/test_errors', action='test_errors')

    with handler_routes(config, views.report.ReportController) as route:
        route('reports', '/reports', action='index')
        route('reports_view', '/reports/{id}', action='view')

    with handler_routes(config, views.settings.SettingsController) as route:
        route('settings', '/settings', action='index')


    return config
