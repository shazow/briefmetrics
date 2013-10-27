from pyramid.request import Request as _Request


__all__ = ['Request']


def _teardown_session(request):
    # Reset the in-memory SQLAlchemy Session cache after each request.
    from briefmetrics.model.meta import Session
    Session.remove()


class Request(_Request):
    DEFAULT_FEATURES = {
        'ssl': True,
    }

    def __init__(self, *args, **kw):
        _Request.__init__(self, *args, **kw)

        self.features = self.DEFAULT_FEATURES.copy()
        self.messages = {}

        # FIXME: Is there a cleaner place to put this?
        self.add_finished_callback(_teardown_session)

    def flash(self, msg, queue='', allow_duplicate=True):
        """
        Similar to request.session.flash(...) but messages only last for the
        duration of the request.
        """
        storage = self.messages.setdefault(queue, [])
        if allow_duplicate or msg not in storage:
            storage.append(msg)

    def pop_flash(self, queue=''):
        return self.messages.pop(queue, [])
