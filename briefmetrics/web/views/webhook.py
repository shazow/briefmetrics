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
        token, id = self.request.matchdict['token'].split('-', 1)

        if service != 'google':
            raise httpexceptions.HTTPNotFound('Service webhook handler not found: {}'.format(service))

        w = model.Webhook.get_by(id=id, token=token)
        if not w:
            raise httpexceptions.HTTPNotFound('Webhook handler not found.')

        # TODO: use tasks.service.stripe_webhook
