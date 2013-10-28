import datetime

from briefmetrics import api
from briefmetrics.web.environment import Response
from briefmetrics.lib.controller import Controller

class ReportController(Controller):

    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account.reports')

        if not user.account.reports:
            return self._redirect(self.request.route_path('settings'))

        # TODO: Handle arbitrary reports
        report = user.account.reports[0]

        # Last Sunday
        date_start = datetime.date.today()
        date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week

        context = api.report.fetch_weekly(self.request, report, date_start)
        html = api.report.render_weekly(self.request, user, context)

        if self.request.params.get('send'):
            message = api.email.create_message(self.request,
                to_email=user.email,
                subject=context.subject, 
                html=html,
            )
            api.email.send_message(self.request, message)

        return Response(html)
