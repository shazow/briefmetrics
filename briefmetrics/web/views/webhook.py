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


def handle_namecheap(request, data):
    event_token = data.get('event_token')
    if not event_token:
        return

    nc_api = service_registry['namecheap'].instance

    # Get event details
    r = nc_api.request('GET', '/v1/saas/saas/event/{token}'.format(event_token))

    data = r.json()
    event_id = data['event']['id']
    return_uri = data['event']['returnURI']
    subscription_id = data['event']['subscription_id']

    email, first_name, last_name, remote_id = get_many(data['event']['user'], ['email', 'first_name', 'last_name', 'id'])
    display_name = [first_name, last_name].join(' ')

    user = api.account.get_or_create(
        email=email,
        service='namecheap',
        display_name=display_name,
        remote_id=remote_id,
        remote_data=data['event']['user'],
    )
    account = user.accounts[0]

    user.set_payment('namecheap', subscription_id)
    model.Session.commit()

    # Confirm event, activate subscription
    ack = {
        'type': 'subscription_create_resp',
        'id': event_id,
        'response': {
            'state': 'Active',
            'provider_id': nc_api.config['client_id'],
        }
    }
    r = nc.session.request('PUT', return_uri, json=ack)

    log.info('namecheap webhook: Provisioned %s' % user)


# TODO: Should this live in lib.service?
webhook_handlers = {
    'stripe': handle_stripe,
    'namecheap': handle_namecheap,
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
