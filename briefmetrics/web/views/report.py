import datetime

from briefmetrics import api, model
from briefmetrics.web.environment import Response, httpexceptions
from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.exceptions import APIError

class ReportController(Controller):

    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account.reports')

        oauth = api.google.auth_session(self.request, user.account.oauth_token)
        try:
            self.c.available_profiles = api.google.Query(oauth).get_profiles(account_id=user.account.id)
        except APIError as e:
            r = e.response.json()
            for msg in r['error']['errors']:
                self.request.flash('Error: %s' % msg['message'])

            self.c.available_profiles = []

        self.c.user = user
        self.c.reports = user.account.reports

        return self._render('reports.mako')


    def view(self):
        user = api.account.get_user(self.request, required=True, joinedload='account')
        report_id = self.request.matchdict['id']

        q = model.Session.query(model.Report).filter_by(id=report_id)
        if not user.is_admin:
            q = q.filter_by(account_id=user.account.id)

        report = q.first()
        if not report:
            raise httpexceptions.HTTPNotFound()

        # Last Sunday
        date_start = datetime.date.today() - datetime.timedelta(days=6) # Last week
        date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week

        report_context = api.report.fetch_weekly(self.request, report, date_start)

        html = api.report.render(self.request, 'email/report.mako', Context({
            'report': report_context,
            'user': user,
        }))

        if self.request.params.get('send'):
            message = api.email.create_message(self.request,
                to_email=user.email,
                subject=report_context.get_subject(), 
                html=html,
            )
            api.email.send_message(self.request, message)

        return Response(html)
