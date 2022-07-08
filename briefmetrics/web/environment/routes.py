from briefmetrics.web import views
from contextlib import contextmanager


@contextmanager
def handler_routes(config, handler):
    "Helper for adding a bulk of routes per handler."
    def _wrapper(route_name, pattern, action=None, **kw):
        config.add_handler(route_name, pattern, handler=handler, action=action, **kw)
    yield _wrapper


def add_routes(config):
    config.add_route('api', '/api')
    config.add_view(views.api.index, route_name='api')

    with handler_routes(config, views.index.IndexController) as route:
        route('index', '/', action='index')
        route('pricing', '/pricing', action='pricing')
        route('about', '/about', action='about')
        route('privacy', '/privacy', action='privacy')
        route('terms', '/terms', action='terms')
        route('security', '/security', action='security')
        route('features', '/features', action='features')
        route('feature', '/features/{id}', action='features')
        route('articles', '/articles/{id}', action='articles')
        route('sitemap', '/sitemap.xml', action='sitemap')

    with handler_routes(config, views.webhook.WebhookController) as route:
        route('webhook', '/webhook/{service}', action='index')

    with handler_routes(config, views.account.AccountController) as route:
        route('account_login', '/account/login/{service}', action='login')
        route('account_logout', '/account/logout', action='logout')
        route('account_connect', '/account/connect/{service}', action='connect')
        route('account_disconnect', '/account/disconnect', action='disconnect')
        route('account_delete', '/account/delete', action='delete')
        route('_account_login_old', '/account/login', action='login')

    with handler_routes(config, views.admin.AdminController) as route:
        route('admin', '/admin', action='index')
        route('admin_health', '/admin/health', action='health')
        route('admin_user', '/admin/user/{id}', action='user')
        route('admin_report_log', '/admin/report_log/{id}', action='report_log')
        route('admin_explore_api', '/admin/explore_api', action='explore_api')
        route('admin_login_as', '/admin/login_as', action='login_as')
        route('admin_test_errors', '/admin/test_errors', action='test_errors')
        route('admin_test_notify', '/admin/test_notify', action='test_notify')

    with handler_routes(config, views.report.ReportController) as route:
        route('reports', '/reports', action='index')
        route('reports_view', '/reports/{id}', action='view')

    with handler_routes(config, views.settings.SettingsController) as route:
        route('settings', '/settings', action='index')


    return config
