from briefmetrics.lib.controller import Controller

def default(exc, request):
    ctrl = Controller(request=request)
    ctrl.c.exc = exc
    return ctrl._render('error.mako')
