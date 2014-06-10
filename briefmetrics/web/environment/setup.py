from pyramid import tweens, httpexceptions

from briefmetrics.lib.exceptions import LoginRequired, APIError


def _dict_view_prefixed(d, prefix):
    return {key[len(prefix):]: d[key] for key in d if key.startswith(prefix)}


def _setup_features(RequestCls, settings, prefix='features.'):
    settings_features = _dict_view_prefixed(settings, prefix)
    RequestCls.DEFAULT_FEATURES.update(settings_features)


def _setup_api(settings):
    from briefmetrics import api

    api.google.GoogleAPI.config.update(_dict_view_prefixed(settings, 'api.google.'))
    api.stripe.StripeAPI.config.update(_dict_view_prefixed(settings, 'api.stripe.'))

    import stripe
    stripe.api_key = settings['api.stripe.client_secret']


def _setup_models(settings):
    """ Attach connection to model modules. """
    if not settings:
        return

    from sqlalchemy import engine_from_config
    from briefmetrics import model

    engine = engine_from_config(settings, 'sqlalchemy.')
    model.init(engine)

    if settings.get('testing'):
        # Show unicode warnings as errors in testing.
        import warnings
        warnings.filterwarnings('error')

def _setup_cache_regions(settings):
    from briefmetrics.lib import cache
    if not hasattr(cache.ReportRegion, 'backend'):
        # Hacky to avoid configuring multiple times in tests and such :(
        cache.ReportRegion.configure_from_config(settings, 'cache.report.')

def _setup_celery(settings):
    from briefmetrics.tasks import setup as tasks_setup
    tasks_setup.init(settings)
    tasks_setup.celery.control.broadcast('pool_restart', arguments={'reload': True})

def _login_tween(handler, registry):
    def _login_handler(request):
        try:
            return handler(request)
        except LoginRequired, e:
            next = request.route_url('account_login', _query={'next': e.next or '/'})
            raise httpexceptions.HTTPSeeOther(next)
        except APIError, e:
            raise httpexceptions.HTTPBadRequest(detail=e.message)

    return _login_handler


def make_config(settings):
    from pyramid.config import Configurator
    return Configurator(settings=settings)


def setup_config(config):
    """ Called by setup with a config instance. Or used for initializing tests
    environment."""
    from .request import Request
    config.set_request_factory(Request)
    config.add_tween('briefmetrics.web.environment.setup._login_tween', over=tweens.MAIN)

    settings = config.get_settings()

    # Add Pyramid plugins
    config.include('pyramid_mako') # Templates
    config.include('pyramid_handlers') # Handler-based routes
    config.include('pyramid_mailer') # Email

    # Beaker sessions
    from pyramid_beaker import session_factory_from_settings
    config.set_session_factory(session_factory_from_settings(settings))

    # Routes
    config.add_static_view("static", "briefmetrics.web:static")

    # More routes
    from .routes import add_routes
    add_routes(config)

    # Module-level model global setup
    _setup_models(settings)

    # Figure out which features are enabled by default
    _setup_features(Request, settings)

    # Set API key values from config
    _setup_api(settings)

    # Load configuration for cache regions
    _setup_cache_regions(settings)

    # Setup Celery
    _setup_celery(settings)

    # Need more setup? Do it here.
    # ...

    return config


def setup_wsgi(global_config, **settings):
    """ This function returns a Pyramid WSGI application.  """
    settings.update(global_config)
    config = setup_config(make_config(settings=settings))
    config.commit()

    return config.make_wsgi_app()


def setup_testing(**settings):
    from pyramid import testing

    # FIXME: Remove the Registry-related stuff once
    # https://github.com/Pylons/pyramid/issues/856 is fixed.
    from .request import Request
    from pyramid.registry import Registry
    registry = Registry('testing')
    request = Request.blank('/') 
    config = testing.setUp(registry=registry, settings=settings, request=request)
    config.registry = registry
    config.setup_registry(settings=settings)

    return setup_config(config)


def setup_shell(env):
    """ Called by pshell. """
    from webtest import TestApp
    env['testapp'] = TestApp(env['app'])

    from briefmetrics.tasks.setup import celery
    celery.request = env['request']
