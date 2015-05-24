import os
import re

from briefmetrics import api
from briefmetrics.lib.pricing import Plan, PlanGroup
from briefmetrics.lib.controller import Controller
from briefmetrics.web.environment import httpexceptions

from mako.exceptions import TopLevelLookupException


RE_IS_SLUG = re.compile('^[\w\-_]+$')


class IndexController(Controller):
    def index(self):
        user_id = api.account.get_user_id(self.request)

        if user_id and not 'landing' in self.request.params:
            return self._redirect(self.request.route_path('reports'))

        return self._render('index.mako')

    def pricing(self):
        self.c.user = api.account.get_user(self.request)

        p = self.c.user and self.c.user.payment
        if p and p.id == 'namecheap':
            return httpexceptions.HTTPSeeOther('https://www.namecheap.com/apps/subscriptions')

        monthly = ('monthly', 'Pay Monthly', [
            Plan.get('starter'),
            PlanGroup.get('agency-10'),
            PlanGroup.get('enterprise'),
        ])
        yearly = ('yearly', 'Pay Yearly (2 month discount)', [
            Plan.get('starter-yr'),
            PlanGroup.get('agency-10-yr'),
            PlanGroup.get('enterprise-yr'),
        ])

        self.c.plans = []

        if self.c.user and self.c.user.payment and self.c.user.payment.id == 'namecheap':
            self.c.plans.append(yearly)
        else:
            self.c.plans.append(monthly)

        if 'yearly' in self.request.params:
            self.c.plans = [yearly, monthly]

        return self._render('pricing.mako')

    def about(self):
        self.title = "About"
        return self._render('about.mako')

    def privacy(self):
        self.title = "Privacy Policy"
        return self._render('privacy.mako')

    def terms(self):
        self.title = "Terms of Service"
        return self._render('terms.mako')

    def security(self):
        self.title = "Security"
        return self._render('security.mako')

    def articles(self):
        template_name = os.path.basename(self.request.matchdict['id'])
        if not RE_IS_SLUG.match(template_name):
            raise httpexceptions.HTTPNotFound('Article does not exist: {}'.format(template_name))

        try:
            return self._render('articles/{}.mako'.format(template_name))
        except TopLevelLookupException:
            raise httpexceptions.HTTPNotFound('Article does not exist: {}'.format(template_name))

    def features(self):
        template_name = os.path.basename(self.request.matchdict['id'])
        try:
            return self._render('features/{}.mako'.format(template_name))
        except TopLevelLookupException:
            raise httpexceptions.HTTPNotFound('Article does not exist: {}'.format(template_name))
