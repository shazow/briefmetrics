from sqlalchemy import orm
from unstdlib import get_many, groupby_count
from datetime import date, timedelta

from briefmetrics import api, model, tasks
from briefmetrics.lib.controller import Controller
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.web.environment import httpexceptions

from .api import expose_api


class WebhookController(Controller):
    def index(self):
        service = self.request.matchdict['service']
        if service != 'stripe':
            raise httpexceptions.HTTPNotFound('Service webhook handler not found: {}'.format(service))

        data = self.request.json
        if not data['livemode']:
            return

        remote_id = data['user_id']
        accounts = model.Session.query(model.Account).filter_by(remote_id=remote_id, service=service)
        if not accuonts:
            raise httpexceptions.HTTPNotFound('Account handler not found.')

        for a in account:
            for ga_tracking_id in a.config.get('ga_funnels', []):
                tasks.service.stripe_webhook.delay(ga_tracking_id, a.id, data)
