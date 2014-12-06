from briefmetrics.lib import service
from briefmetrics.lib.service.heap import collect as heap_collect, extract as heap_extract
from celery.utils.log import get_task_logger

from briefmetrics import api
from briefmetrics import model

from .setup import celery


log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def stripe_webhook(ga_tracking_id, stripe_account_id, data, pretend=False):
    """Task to send a specific weekly report (gets created by send_all)."""
    stripe_account = model.Account.get_by(id=stripe_account_id, service='stripe')
    if not stripe_account:
        log.warn('Invalid stripe account webhook, skipping: %s' % stripe_account_id)
        return

    stripe_query = api.account.query_service(celery.request, stripe_account)
    t = stripe_query.extract_transaction(data)
    service.registry['google'].inject_transaction(ga_tracking_id, t, pretend=pretend)

    # Pipe to Heap, hardcoded for meow:
    if ga_tracking_id != 'UA-407051-16' or pretend:
        return

    heap_collect(
        app_id=1675620903,
        identity=t['user_id'],
        event='Revenue',
        properties=heap_extract(t),
    )
