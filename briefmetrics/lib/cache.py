import inspect

from dogpile.cache import make_region, register_backend
from dogpile.cache.api import CacheBackend, NO_VALUE


# Note: This lives in https://gist.github.com/shazow/6838337

def make_key_generator(namespace, fn, value_mangler=str, arg_blacklist=('self', 'cls')):
    """
    Create a cache key generator for function calls of fn.

    :param namespace:
        Value to prefix all keys with. Useful for differentiating methods with
        the same name but in different classes.

    :param fn:
        Function to create a key generator for.

    :param value_mangler:
        Each value passed to the function is run through this mangler.
        Default: str

    :param arg_blacklist:
        Iterable of arguments to ignore when creating a key.

    Returns a function which can be called with the same arguments as fn but
    returns a corresponding key for that call.

    Note: Ingores fn(..., *arg, **kw) parameters.
    """
    # TODO: Include parent class in name?
    # TODO: Handle vararg and kw?
    # TODO: Better default value_mangler?
    fn_args = inspect.signature(fn).parameters.keys()
    arg_blacklist = arg_blacklist or []

    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    def generate_key(*arg, **kw):
        kw.update(zip(fn_args, arg))

        for arg in arg_blacklist:
            kw.pop(arg, None)

        key = namespace + '|' + ' '.join(value_mangler(kw[k]) for k in sorted(kw))
        return key

    return generate_key


ReportRegion = make_region(
    function_key_generator=make_key_generator,
)


# TODO: Remove, obsolete by dogpile.cache.null
class DisabledBackend(CacheBackend):
    def __init__(self, arguments):
        pass

    def get(self, key):
        return NO_VALUE

    def set(self, key, value):
        pass

    def delete(self, key):
        pass

register_backend("DisabledBackend", "briefmetrics.lib.cache", "DisabledBackend")
