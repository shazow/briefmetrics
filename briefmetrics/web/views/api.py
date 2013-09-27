import json

from unstdlib import iterate
from functools import wraps

from briefmetrics.web.environment import httpexceptions, Response
from briefmetrics.lib.exceptions import APIControllerError, LoginRequired
from briefmetrics.model.meta import SchemaEncoder


API_METHOD_MAP = {}

def expose_api(name, check_csrf=True, check_referer=True):
    """ Decorator helper for registering an exposed API method.

    The decorator does not wrap any logic to the function, but merely attaches
    properties which affect how `api_controller` processes the requested
    method.

    :param name:
        Method name which will be exposed from the `/api` route. For example,
        if "foo", then it will be accessible from `/api?method=foo`.

    :param check_csrf:
        If True, check that a CSRF token is included in the request and is
        correct to the request's session. (Default: True)

    :param check_referer:
        If True and the request has a referer, check that the request's referer
        is relative to the origin host. (Default: True)
    """
    def decorator(fn):
        API_METHOD_MAP[name] = fn
        fn.exposed_name = name
        fn.check_csrf = check_csrf
        fn.check_referer = check_referer
        return fn
    return decorator


def handle_api(method_whitelist=None):
    """ Decorator helper for handling exposed API methods in views.

    Class view methods which are marked to `handle_api` will run the request
    through `api_controller` when a request looks like an api request. If an
    `APIControllerError` is raised, then the original view will subsequently be
    executed to allow for error handling.

    All successful requests here are assumed to be `format=redirect`.

    :param method_whitelist:
        Restrict API handling to these specified methods. If None, then all
        API methods are handled. (Default: None)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(self):
            if 'method' not in self.request.params:
                return fn(self)

            try:
                api_controller(self.request, method_whitelist=method_whitelist)
            except APIControllerError, e:
                self.request.session.flash(e.message)
                return fn(self)

            next = self.request.params.get('next') or self.request.referer
            return httpexceptions.HTTPSeeOther(next)

        return wrapped

    return decorator


def api_controller(request, method_whitelist=None):
    """ Performs the internal exposed API routing and error handling.

    :param request:
        Request object.

    :param method_whitelist:
        If provided, limits the methods which we're allowed to process in this
        call. Can be a single method name string, or a list of them.
    """
    try:
        method = request.params['method']
    except KeyError, e:
        raise APIControllerError("Missing required parameter: %s" % e.args[0])

    if method_whitelist and method not in iterate(method_whitelist):
        raise APIControllerError("Method not permitted: %s" % method)

    fn = API_METHOD_MAP.get(method)
    if not fn:
        raise APIControllerError("Method does not exist: %s" % method)

    if fn.check_referer and request.referer:
        expected_referer = request.application_url.split('://', 1)[1]
        request_referer = request.referer.split('://', 1)[1]

        if not request_referer.startswith(expected_referer):
            raise APIControllerError("Bad referer: %s" % request.referer)

    if fn.check_csrf and request.params.get('csrf_token') != request.session.get_csrf_token():
        raise APIControllerError("Invalid csrf_token value: %s" % request.params.get('csrf_token'))

    try:
        return fn(request)
    except KeyError, e:
        raise APIControllerError("Missing required parameter: %s" % e.args[0])


def index(request):
    """ The only app-routed view which delegates the rest of the API-related
    functionality. Collates the API result into the final payload and response
    object.

    This is bypassed if the API method is processed through a @handle_api view.
    """
    data = {
        'status': 'ok',
        'code': 200,
        'messages': [],
        'result': {},
    }

    format = request.params.get('format', 'json')
    if format not in ('json', 'redirect'):
        return httpexceptions.HTTPBadRequest('Invalid format requested: %s' % format)

    encode_settings = {'cls': SchemaEncoder}
    if request.params.get('pretty'):
        encode_settings['sort_keys'] = True
        encode_settings['indent'] = 4

    next = request.params.get('next') or request.referer

    try:
        r = api_controller(request)
        if r is not None:
            data['result'] = r

    except (APIControllerError, LoginRequired), e:
        data['messages'] += [e.message]
        data['code'] = e.code
        data['status'] = 'error'

        if isinstance(e, LoginRequired):
            query = {'next': e.next or next}
            next = request.route_url('account_login', _query=query)

    data['messages'] += request.pop_flash()

    if format == 'redirect':
        for message in data['messages']:
            # Copy request-level messages to session storage to be displayed on
            # redirect.
            request.session.flash(message)
        return httpexceptions.HTTPSeeOther(next or '/')

    body = json.dumps(data, **encode_settings)
    return Response(body, content_type='application/json', status=data['code'])


# Exposed APIs:

@expose_api('ping')
def ping(request):
    return {'ping': 'pong'}
