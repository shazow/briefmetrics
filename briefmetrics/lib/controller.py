from collections import defaultdict

from briefmetrics.web.environment import render_to_response, render
from briefmetrics.web.environment import httpexceptions

from . import helpers as h
from . import pricing


class Context(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class DefaultContext(defaultdict):
    __getattr__ = defaultdict.__getitem__
    __setattr__ = defaultdict.__setitem__


class Controller(object):
    """
    This base class can be used in two ways:

    1. You can use it as a handler base class as defined in pyramid_handlers.

    2. You can use it as a singular route handler if you provide a __call__
    definition with the route logic which returns a response.
    """
    DEFAULT_NEXT = '/'
    track_analytics = True

    def __init__(self, request, context=None):
        self.title = None
        self.request = request
        self.session = request.session
        self.context = self.c = context or Context()
        self.default = DefaultContext(str)

        self.previous_url = request.referer
        self.current_path = request.path_qs
        self.next = request.params.get('next')

        # Prevent cross-site forwards (possible exploit vector).
        if not self.next or self.next.startswith('//') or '://' in self.next:  # Can we do this better?
            self.next = self.DEFAULT_NEXT

    def _add_defaults(self, *param_args, **kw):
        """
        Pull in user-supplied parameter values into a defaultdict to use for
        pre-filled forms.
        """
        for param in param_args:
            self.default[param] = self.request.params.get(param, self.default.get(param, ''))

        self.default.update(kw)

    def _default_render_values(self):
        """
        Return a dictionary representing the template's default root variable
        namespace.
        """
        request = self.request
        login_url = request.route_path('account_login', service='google')
        if request.features.get('ssl'):
            login_url = request.route_url('account_login', service='google', _scheme='https')

        try:
            current_route = request.current_route_path(_query=None)
        except ValueError:
            # Tests and tasks have no current route. TODO: Maybe fix this somehow?
            current_route = u'/'

        track_analytics = self.track_analytics
        if request.features.get('offline') or request.host.startswith('localhost'):
            track_analytics = False

        return {
            'h': h,
            'c': self.context,
            'default': self.default,
            'features': request.features,
            'request': request,
            'session': request.session,
            'settings': request.registry.settings,
            'title': self.title,
            'is_logged_in': 'user_id' in self.session,
            'track_analytics': track_analytics,
            'current_path': self.current_path,
            'current_route': current_route,
            'previous_url': self.previous_url,
            'next_url': self.next,

            # App-specific
            'pricing': pricing,
            'login_url': login_url,
        }

    def _get_render_values(self, extra_values=None):
        """
        Return a dictionary represengin the template's default root variable
        namespace with any additional overrides.
        """
        value = self._default_render_values()
        if extra_values:
            value.update(extra_values)
        return value

    def _render(self, renderer_name, extra_values=None, package=None):
        """
        Return a rendered Response object.
        """
        value = self._get_render_values(extra_values=extra_values)
        return render_to_response(renderer_name, value=value, request=self.request, package=package)

    def _render_template(self, renderer_name, extra_values=None, package=None):
        """
        Return a rendered HTML blob.
        """
        value = self._get_render_values(extra_values=extra_values)
        return render(renderer_name, value=value, request=self.request, package=package)

    def _redirect(self, *args, **kw):
        "Shortcut for returning HTTPSeeOther"
        return httpexceptions.HTTPSeeOther(*args, **kw)

    def _respond(self):
        "Override this to implement the view's global response behavior."
        raise NotImplemented('View response not implemented: %s' % self.__class__.__name__)
