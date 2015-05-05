import logging
import json

from sqlalchemy import orm
from unstdlib import get_many, now

from briefmetrics import api, model, tasks
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.controller import Controller
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.web.environment import httpexceptions, Response


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
    try:
        r = nc_api.request('GET', '/v1/saas/saas/event/{token}'.format(token=event_token))
    except Exception as e:
        log.error('namecheap webhook: Failed token lookup: %s' % event_token)
        raise

    data = r.json()
    fn = {
        'subscription_create': _namecheap_subscription_create,
        'subscription_alter': _namecheap_subscription_alter,
        'subscription_cancel': _namecheap_subscription_cancel,
    }.get(data['type'])

    if not fn:
        raise httpexceptions.HTTPBadRequest('Invalid event type: %s' % data['type'])

    log.debug("namecheap webhook: Processing %s: %s" % (data['type'], data['event']))

    try:
        return fn(request, data)
    except Exception as e:
        log.error('namecheap webhook: Failed %s (%s): %s' % (data['type'], e, event_token))
        raise


def _namecheap_subscription_create(request, data):
    nc_api = service_registry['namecheap'].instance

    event_id = data['event']['id']
    return_uri = data['event'].get('returnURI')
    subscription_id = data['event']['subscription_id']

    email, first_name, last_name, remote_id = get_many(data['event']['user'], ['email', 'first_name', 'last_name', 'username'])
    display_name = ' '.join([first_name, last_name])
    plan_id = data['event']['order'].get('pricing_plan_sku')

    user = api.account.get_or_create(
        email=email,
        service='namecheap',
        display_name=display_name,
        remote_id=remote_id,
        remote_data=data['event']['user'],
        plan_id=plan_id,
    )

    ack_message = 'Briefmetrics activation instructions sent to %s' % email
    ack_state = 'Active'

    if user.payment and user.payment.is_charging:
        ack_message = 'Failed to provision new Briefmetrics account for {email}. Account already exists with payment information.'.format(email=email)
        ack_state = 'Failed'
        log.info('namecheap webhook: Provision skipped %s' % user)
    else:
        user.set_payment('namecheap', subscription_id)
        if user.payment.auto_charge:
            user.time_next_payment = now() + user.payment.auto_charge
        model.Session.commit()
        log.info('namecheap webhook: Provisioned %s' % user)

    ack = {
        'type': 'subscription_create_resp',
        'id': event_id,
        'response': {
            'state': ack_state,
            'provider_id': user.id,
            'message': ack_message,
        }
    }

    if return_uri:
        # Confirm event, activate subscription
        r = nc_api.session.request('PUT', return_uri, json=ack) # Bypass our wrapper
        assert_response(r)

    if ack_state != 'Active':
        return ack

    subject = u"Welcome to Briefmetrics"
    html = api.email.render(request, 'email/welcome_namecheap.mako')
    message = api.email.create_message(request,
        to_email=email,
        subject=subject,
        html=html,
    )
    api.email.send_message(request, message)
    return ack


def _namecheap_subscription_cancel(request, data):
    nc_api = service_registry['namecheap'].instance

    event_id = data['event']['id']
    return_uri = data['event'].get('returnURI')
    remote_id = data['event']['user']['username']

    q = model.Session.query(model.Account).filter_by(service='namecheap', remote_id=remote_id)
    q = q.options(orm.joinedload('user'))

    account = q.first()
    if not account:
        raise httpexceptions.HTTPBadRequest('Invalid remote id.')

    user = account
    api.account.delete_payments(account.user)

    log.info('namecheap webhook: Cancelled %s' % user)

    ack = {
        'type': 'subscription_cancel_resp',
        'id': event_id,
        'response': {
            'state': 'Inactive',
        }
    }

    if return_uri:
        # Confirm event, activate subscription
        r = nc_api.session.request('PUT', return_uri, json=ack) # Bypass our wrapper
        assert_response(r)

    return ack


def _namecheap_subscription_alter(request, data):
    nc_api = service_registry['namecheap'].instance

    event_id = data['event']['id']
    return_uri = data['event'].get('returnURI')
    remote_id = data['event']['user']['username']
    order = data['event']['order']

    q = model.Session.query(model.Account).filter_by(service='namecheap', remote_id=remote_id)
    q = q.options(orm.joinedload('user'))

    account = q.first()
    if not account:
        raise httpexceptions.HTTPBadRequest('Invalid remote id.')

    user = account
    api.account.set_plan(account.user, order['pricing_plan_sku'])
    # XXX: Make sure pro-rating happens?

    log.info('namecheap webhook: Altered %s' % user)

    ack = {
        'type': 'subscription_alter_resp',
        'id': event_id,
        'response': {
            'state': 'Active',
        }
    }

    if return_uri:
        # Confirm event, activate subscription
        r = nc_api.session.request('PUT', return_uri, json=ack) # Bypass our wrapper
        assert_response(r)

    return ack


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
        r = handler(self.request, data)
        body = ''
        if r:
            body = json.dumps(r)

        return Response(body, content_type='application/json', status=200)
