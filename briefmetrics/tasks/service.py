from briefmetrics.lib import service
from celery.utils.log import get_task_logger

from briefmetrics import model

from .setup import celery


log = get_task_logger(__name__)


def _pretend_collect(*args, **kw):
    print "pretend_collect:", args, kw


@celery.task(ignore_result=True)
def stripe_webhook(ga_tracking_id, stripe_account_id, data, pretend=False):
    """Task to send a specific weekly report (gets created by send_all)."""
    kw = {}
    if pretend:
        kw['collect_fn'] = _pretend_collect

    stripe_account = model.Account.get_by(id=stripe_account_id, service='stripe')
    if not stripe_account:
        log.warn('Invalid stripe account webhook, skipping: %s' % stripe_account_id)
        return

    stripe_api = service.registry['stripe'](celery.request, stripe_account)

    t = stripe_api.extract_transaction(data)
    service.registry['google'].inject_transaction(ga_tracking_id, t, **kw)
