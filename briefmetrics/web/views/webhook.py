import logging
import operator

from sqlalchemy import orm
from unstdlib import get_many, groupby_count
from datetime import date, timedelta

from briefmetrics import api, model, tasks
from briefmetrics.lib.controller import Controller
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.web.environment import httpexceptions, Response

from .api import expose_api


log = logging.getLogger(__name__)


def handle_stripe(request, data):
    if not data['livemode']:
        return

    if data['type'] != "invoice.payment_succeeded":
        return

    if not data['data']['object']['total']:
        # Shortcut for empty totals (free accounts)
        return

    remote_id = data['user_id']
    accounts = model.Session.query(model.Account).filter_by(remote_id=remote_id, service='stripe')
    if not accounts:
        raise httpexceptions.HTTPNotFound('Account handler not found.')

    has_funnels = any(a.config.get('ga_funnels') for a in accounts)
    if not has_funnels:
        return

    # Validate webhook
    stripe_query = api.account.query_service(request, accounts[0])
    event_data = stripe_query.validate_webhook(data)
    if not event_data:
        raise httpexceptions.HTTPBadRequest('Webhook failed to validate: %s' % data['id'])

    count = 0
    for a in accounts:
        for ga_tracking_id in a.config.get('ga_funnels', []):
            count += 1
            tasks.service.stripe_webhook.delay(ga_tracking_id, a.id, event_data)

    log.info('stripe webhook: Queued %d funnels for account: %s' % (count, a.id))


# TODO: Should this live in lib.service?
webhook_handlers = {
    'stripe': handle_stripe,
}


class WebhookController(Controller):
    def index(self):
        service = self.request.matchdict['service']
        handler = webhook_handlers[service]

        if not handler:
            raise httpexceptions.HTTPNotFound('Service webhook handler not found: {}'.format(service))

        data = self.request.json
        handler(self.request, data)

        return Response('', content_type='application/json', status=200)
