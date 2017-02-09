from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks
from briefmetrics.lib.report import get_report, sparse_cumulative, date_to_quarter, quarter_to_dates
from briefmetrics.lib.table import Column
from briefmetrics.lib.controller import Context

from briefmetrics.test.fixtures.api_google import FakeQuery

import mock
import datetime

Session = model.Session


@mock.patch('briefmetrics.lib.service.google.Query', FakeQuery)
class TestReport(test.TestWeb):
    def _create_report(self, user=None, remote_id=None, config=None):
        u = user or api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        if config:
            u.config = config
            Session.commit()

        account = u.accounts[0]
        api_query = api.account.query_service(self.request, account=account)
        remote_data = api_query.get_profiles()[0]
        report = api.report.create(account.id, remote_data=remote_data, remote_id=remote_id, display_name=u'example.com', subscribe_user_id=u.id)
        Session.commit()
        return report

    def test_fake_query(self):
        account = model.Account.create(service='google')
        Session.commit()

        q = api.account.query_service(self.request, account=account)

        r = q.get_profile()
        self.assertEqual(r[u'websiteUrl'], u'example.com')

        q = api.account.query_service(self.request, account=account)
        r = q.get_profile()
        self.assertEqual(r[u'websiteUrl'], u'example.com')

        t = q.get_table({'max-results': 5}, dimensions=[
            Column('ga:pagePath'),
        ], metrics=[
            Column('ga:pageviews', type_cast=int, threshold=0),
            Column('ga:nthWeek'),
        ])
        self.assertEqual(len(t.rows), 5)
        self.assertEqual(t.rows[1].get('ga:pagePath'), '/account/create')
        self.assertEqual(t.rows[1].get('ga:pageviews'), 15001)
        self.assertEqual(t.get('ga:pageviews').max_row[0], 16399)

        t = q.get_table({'max-results': 7}, dimensions=[Column('ga:month')])
        self.assertEqual([list(m) for m in t.iter_rows()], [[u'01']]*6 + [[u'02']]) 

    def test_fetch(self):
        report = self._create_report()

        since_time = datetime.datetime(2013, 1, 13)
        context = api.report.fetch(self.request, report, since_time)
        self.assertEqual(context.date_end, datetime.date(2013, 1, 12))
        self.assertEqual(context.date_next, datetime.date(2013, 1, 21))
        self.assertEqual(context.get_subject(), u'Report for example.com (Jan 6-12)')

        html = api.email.render(self.request, context.template, Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertTrue(html)

    def test_empty(self):
        report = self._create_report()
        google_query = api.account.query_service(self.request, report.account)
        google_query.num_rows = 0

        since_time = datetime.datetime(2013, 1, 13)
        context = api.report.fetch(self.request, report, since_time, api_query=google_query)
        self.assertFalse(context.data)

        # TODO: Test send.
        html = api.email.render(self.request, 'email/error_empty.mako', Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertIn('no results for your site', html)


    def test_send(self):
        report = self._create_report()
        self.assertEqual(report.time_next, None)
        self.assertEqual(model.Report.count(), 1)

        user = report.account.user
        user.num_remaining = 1
        Session.commit()

        tasks.report.celery.request = self.request

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)
            self.assertEqual(len(send_message.call_args_list), 2)

            call = send_message.call_args_list[0]
            message = call[0][1].params
            self.assertIn(u"Report for example.com", message['subject'])

            call = send_message.call_args_list[1]
            message = call[0][1].params
            self.assertEqual(message['subject'], u"Your Briefmetrics trial is over")

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertNotEqual(report.time_next, None)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Send all again, should skip because too early
        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertFalse(send_message.called)

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Reset time and send again
        report.time_next = None
        report.time_expire = datetime.datetime(2010, 1, 1) # Sometime in the past
        Session.commit()

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertFalse(send_message.called)

        # Report should be deleted.
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.ReportLog.count(), 1)

        Session.refresh(user)
        self.assertEqual(user.num_remaining, 0)

    def test_reschedule(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example', config={'preferred_hour': 2})
        account = u.accounts[0]
        api_query = api.account.query_service(self.request, account=account)
        remote_data = api_query.get_profiles()[0]
        remote_id = remote_data['id']

        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))
        r = self.call_api('report.create', remote_id=remote_id)
        report_id = r['result']['report']['id']
        report = model.Report.get(report_id)

        with mock.patch('briefmetrics.api.email.send_message'):
            api.report.send(self.request, report)

        report = model.Report.get(report_id)
        self.assertEqual(report.time_preferred.hour, 2)
        self.assertEqual(report.time_next.hour, 2)

        api.report.reschedule(report_id=report.id, hour=1)
        report = model.Report.get(report_id)
        self.assertEqual(report.time_preferred.hour, 1)
        self.assertEqual(report.time_next.hour, 1)

    def test_expire_then_upgrade(self):
        report = self._create_report(remote_id='foo')
        user = report.account.user
        user.num_remaining = 0
        Session.commit()

        tasks.report.celery.request = self.request

        # Add credit card
        with mock.patch('briefmetrics.lib.payment.stripe.stripe') as stripe:
            stripe.Customer.create().id = 'TEST'
            update_subscription = stripe.Customer.retrieve().update_subscription

            api.account.set_payments(user, plan_id='starter', card_token='FAKETOKEN')
            self.assertEqual(stripe.Customer.create.call_args[1]['card'], 'FAKETOKEN')

            Session.refresh(user)
            self.assertEqual(user.num_remaining, None)
            self.assertEqual(user.stripe_customer_id, 'TEST')

            report = self._create_report(user=user, remote_id='bar')
            with mock.patch('briefmetrics.api.email.send_message') as send_message:
                tasks.report.send_all(async=False)
                self.assertTrue(send_message.called)

            self.assertTrue(update_subscription.called)
            self.assertEqual(update_subscription.call_args[1]['plan'], 'briefmetrics_starter')


    def test_auth_error(self):
        tasks.report.celery.request = self.request

        self._create_report()

        def raise_error(*args, **kw):
            from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
            raise InvalidGrantError()

        with mock.patch('briefmetrics.api.report.fetch', raise_error):
            with mock.patch('briefmetrics.api.email.send_message') as send_message:
                tasks.report.send_all(async=False)
                self.assertTrue(send_message.called)

                call, = send_message.call_args_list
                message = call[0][1].params
                self.assertEqual(message['subject'], u"Problem with your Briefmetrics")

        self.assertEqual(model.Report.count(), 0)

        self._create_report()

        def raise_error(*args, **kw):
            from briefmetrics.lib.exceptions import APIError
            message = "User does not have sufficient permissions for this profile."
            raise APIError("API call failed: %s" % message, 400)

        with mock.patch('briefmetrics.api.report.fetch', raise_error):
            with mock.patch('briefmetrics.api.email.send_message') as send_message:
                tasks.report.send_all(async=False)
                self.assertTrue(send_message.called)

                call, = send_message.call_args_list
                message = call[0][1].params
                self.assertEqual(message['subject'], u"Problem with your Briefmetrics")

        self.assertEqual(model.Report.count(), 0)

    def test_api(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        r = self.app.get('/reports')
        self.assertIn('New report', r)
        self.assertNotIn('Active reports', r)

        r = self.call_api('report.create', remote_id=u'200001', pace='year')
        report = r['result']['report']
        self.assertEqual(report['display_name'], u'example.com')
        self.assertEqual(model.Report.count(), 1)
        self.assertEqual(model.Report.get(report['id']).config, {u'pace': u'year'})

        r = self.app.get('/reports')
        self.assertIn('Active reports', r)

        r = self.call_api('report.delete', report_id=report['id'])
        self.assertEqual(model.Report.count(), 0)

    def test_limits(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        # Limit number of sites & recipients
        u = model.User.get(1)
        u.config['num_recipients'] = 1
        u.config['num_sites'] = 1
        Session.commit()

        r = self.call_api('report.create', remote_id=u'200001', type='week')
        report_id = r['result']['report']['id']

        # Same site twice is cool
        r = self.call_api('report.create', remote_id=u'200001', type='month')

        # Different site exceeds site limit
        r = self.call_api('report.create', _status=400, remote_id=u'200002')

        # Adding a subscriber to the first report also exceeds
        r = self.call_api('subscription.create', _status=400, report_id=report_id, email='foo@example.com', display_name='Foo')

        self.assertEqual(model.User.count(), 1)
        self.assertEqual(model.Report.count(), 2)

        u = model.User.get(1)
        u.config['num_recipients'] = 2
        u.config['num_sites'] = 2
        Session.commit()

        r = self.call_api('report.create', remote_id=u'200002')
        r = self.call_api('subscription.create', report_id=report_id, email='foo@example.com', display_name='Foo')

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Report.count(), 3)

    def test_combine(self):
        u1 = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example', plan_id='agency-10')
        u2 = api.account.get_or_create(email=u'bono@example.com', token={}, display_name=u'Bono')
        account = u1.accounts[0]

        api_query = api.account.query_service(self.request, account=account)

        r1 = model.Report.create(account=account, remote_data=api_query.get_profiles()[0], display_name=u'example.com', type='week')
        model.Subscription.create(user=u1, report=r1)
        model.Subscription.create(user=u2, report=r1)

        r2 = model.Report.create(account=account, remote_data=api_query.get_profiles()[1], display_name=u'bar.example.com', type='week')
        model.Subscription.create(user=u1, report=r2)

        Session.commit()

        report = api.report.combine(report_ids=[r1.id, r2.id], is_replace=False, account_id=account.id)
        display_name = report.display_name
        self.assertEqual(len(report.remote_data['combined']), 2)
        self.assertEqual(report.remote_data['combined'][0]['id'], '200000')
        self.assertEqual(report.remote_data['combined'][1]['id'], '200001')
        self.assertEqual(report.display_name, 'example.com, bar.example.com')
        Session.delete(report)
        Session.commit()

        r = self.call_api('account.login', token=u'%s-%d' % (u1.email_token, u1.id))
        r = self.call_api('report.combine', report_ids=[r1.id, r2.id])

        self.assertEqual(r['result']['report']['display_name'], display_name)

        r = self.app.get('/reports/%s' % r['result']['report']['id'])

    def test_whitelabel(self):
        report = self._create_report()
        user = report.account.user
        user.config = {
            "email_intro_text": "foo bar",
            "email_header_image": "localhost.gif",
            "reply_to": "support@localhost.com",
            "from_link": "http://www.localhost.com/",
            "from_name": "Local Host Design",
            "from_email": "from@localhost.com",
            "style_a_color": "#7688c9",
            "style_permalink_color": "#7688c9",
            "style_thead_background": "#eeeeee",
            "style_sub_a_color": "#ccc",
            "hide_briefmetrics": True,
            "api_mailgun_key": "YYY",
        }
        user.num_remaining = 10
        Session.commit()

        tasks.report.celery.request = self.request

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)
            self.assertEqual(len(send_message.call_args_list), 1)

            call = send_message.call_args_list[0]
            message = call[0][1].params
            self.assertIn(u"Report for example.com", message['subject'])
            self.assertNotIn(u'<a href="https://briefmetrics.com">Briefmetrics</a>', message['html'])

            if 'from_email' in message:
                # Mandrill
                self.assertEqual(u"from@localhost.com", message['from_email'])
            else:
                # Mailgun
                self.assertEqual(u"Local Host Design <from@localhost.com>", message['from'])

            self.assertEqual(
                "Your site had 16,012 views this week (+6.74% over last week).",
                message['text'].split('\n')[0])

        self.assertEqual(model.Report.count(), 1)

    def test_mandrill(self):
        report = self._create_report()
        user = report.account.user
        user.config = {
            "api_mandrill_key": "YYY",
        }
        user.num_remaining = 10
        Session.commit()

        tasks.report.celery.request = self.request

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)
            self.assertEqual(len(send_message.call_args_list), 1)

            call = send_message.call_args_list[0]
            message = call[0][1].params
            self.assertIn(u"Report for example.com", message['subject'])

            # Mandrill auto-generates text, so there won't be a text field
            self.assertNotIn(u'text', message)
            self.assertIn(u'from_email', message)


class TestReportModel(test.TestCase):

    def test_encode_preferred(self):
        self.assertEqual(model.Report.encode_preferred_time(), datetime.datetime(1900, 1, 1, 13, 0, 0)) # Default
        self.assertEqual(model.Report.encode_preferred_time(hour=8, minute=15), datetime.datetime(1900, 1, 1, 8, 15, 0))
        self.assertEqual(model.Report.encode_preferred_time(hour=0, minute=0, second=0), datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(model.Report.encode_preferred_time(weekday=0).date(), datetime.date(1900, 1, 8)) # Monday
        self.assertEqual(model.Report.encode_preferred_time(weekday=6).date(), datetime.date(1900, 1, 14)) # Sunday

    def test_next_preferred(self):
        now = datetime.datetime(2013, 1, 1, 7, 35, 15) # Tuesday

        r = get_report('day')(model.Report(), now)
        r.report.set_time_preferred(hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 2, 12, 0, 0))

        r = get_report('week')(model.Report(), now)
        # Default to Monday @ 8pm EST for weekly
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 7, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 1, 12)), datetime.datetime(2013, 1, 14, 13)) # Sat -> Mon

        # Wednesdays @ 12pm UTC
        r.report.set_time_preferred(weekday=2, hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 2, 12, 0, 0))

        # Mondays @ 12pm UTC
        r.report.set_time_preferred(weekday=0, hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 7, 12, 0, 0))

        r = get_report('activity-month')(model.Report(), now)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 2, 1, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 2)), datetime.datetime(2013, 3, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 1)), datetime.datetime(2013, 3, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 28)), datetime.datetime(2013, 3, 1, 13))

        now = datetime.datetime(2013, 2, 5, 7, 35, 15) # Tuesday, Jan 2013

        r = get_report('activity-year')(model.Report(), now)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2014, 1, 1, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 1, 1)), datetime.datetime(2014, 1, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2012, 12, 28)), datetime.datetime(2013, 1, 1, 13))

        r = get_report('activity-quarter')(model.Report(), now)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 4, 1, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 1, 1)), datetime.datetime(2013, 4, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2012, 12, 28)), datetime.datetime(2013, 1, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2016, 3, 31)), datetime.datetime(2016, 4, 1, 13))


class TestReportLib(test.TestCase):
    def _create_report_model(self, type='day'):
        return model.Report(
            remote_id=1,
            remote_data={},
            display_name='example.com',
            type=type,
        )

    def test_daily(self):
        report = self._create_report_model('day')
        since_time = datetime.datetime(2013, 1, 2)

        r = get_report('day')(report, since_time)

        self.assertEqual((r.date_end-r.date_start).days, 0)
        self.assertEqual(r.date_end, datetime.date(2013, 1, 1))
        self.assertEqual(r.date_next, datetime.date(2013, 1, 2))
        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 1)")

    def test_activity_report(self):
        report = self._create_report_model('week')
        since_time = datetime.datetime(2013, 1, 14) # Monday after Next Sunday
        r = get_report('week')(report, since_time)

        self.assertEqual((r.date_end-r.date_start).days, 6)
        self.assertEqual(r.date_start, datetime.date(2013, 1, 6)) # First Sunday
        self.assertEqual(r.date_end, datetime.date(2013, 1, 12)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 1, 21)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 6-12)")

        # Scenario: Overlapping month
        since_time = datetime.datetime(2013, 2, 4) # Monday after Next Saturday
        r = get_report('week')(report, since_time)

        self.assertEqual(r.date_start, datetime.date(2013, 1, 27)) # Last Sunday
        self.assertEqual(r.date_end, datetime.date(2013, 2, 2)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 2, 11)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 27-Feb 2)")

        # Monthly activity report
        since_time = datetime.datetime(2013, 2, 5)
        report = self._create_report_model('activity-month')
        r = get_report('activity-month')(report, since_time)

        self.assertEqual(r.report.type, 'activity-month')
        self.assertEqual(r.date_start, datetime.date(2013, 1, 1)) # Start of the month
        self.assertEqual(r.date_end, datetime.date(2013, 1, 31)) # End of the month
        self.assertEqual(r.date_next, datetime.date(2013, 3, 1)) # First day of next month

        self.assertEqual(r.get_subject(), u"Report for example.com (January)")

        # Yearly activity report
        since_time = datetime.datetime(2013, 2, 5)
        report = self._create_report_model('activity-year')
        r = get_report('activity-year')(report, since_time)

        self.assertEqual(r.report.type, 'activity-year')
        self.assertEqual(r.date_start, datetime.date(2012, 1, 1)) # Start of the month
        self.assertEqual(r.date_end, datetime.date(2012, 12, 31)) # End of the month
        self.assertEqual(r.date_next, datetime.date(2014, 1, 1)) # First day of next month

        self.assertEqual(r.get_subject(), u"Report for example.com (2012)")

        # Quarterly
        since_time = datetime.datetime(2013, 4, 5)
        report = self._create_report_model('activity-quarter')
        r = get_report('activity-quarter')(report, since_time)

        self.assertEqual(r.report.type, 'activity-quarter')
        self.assertEqual(r.date_start, datetime.date(2013, 1, 1)) # Start of the quarter
        self.assertEqual(r.date_end, datetime.date(2013, 3, 31)) # End of the quarter
        self.assertEqual(r.date_next, datetime.date(2013, 7, 1)) # First day of next quarter

        self.assertEqual(r.get_subject(), u"Report for example.com (2013Q1)")

        since_time = datetime.datetime(2013, 2, 5)
        report = self._create_report_model('activity-quarter')
        r = get_report('activity-quarter')(report, since_time)

        self.assertEqual(r.report.type, 'activity-quarter')
        self.assertEqual(r.date_start, datetime.date(2012, 10, 1)) # Start of the quarter
        self.assertEqual(r.date_end, datetime.date(2012, 12, 31)) # End of the quarter
        self.assertEqual(r.date_next, datetime.date(2013, 4, 1)) # First day of next quarter

        self.assertEqual(r.get_subject(), u"Report for example.com (2012Q4)")



    def test_trends_report(self):
        report = self._create_report_model('month')
        report.set_time_preferred(weekday=0) # Preferred time: First Monday

        since_time = datetime.datetime(2014, 1, 6) # First Monday of January 2014
        r = get_report('month')(report, since_time)

        self.assertEqual(r.report.type, 'month')
        self.assertEqual(r.date_start, datetime.date(2013, 12, 1)) # Start of December 2013
        self.assertEqual(r.date_end, datetime.date(2013, 12, 31)) # End of December 2013
        self.assertEqual(r.date_next, datetime.date(2014, 2, 3)) # First Monday of February 2014

        self.assertEqual(r.get_subject(), u"Report for example.com (December)")

        # Scenario: Month starting with Monday (Sept 1)
        since_time = datetime.datetime(2014, 8, 4)
        r = get_report('month')(report, since_time)

        self.assertEqual(r.date_start, datetime.date(2014, 7, 1))
        self.assertEqual(r.date_end, datetime.date(2014, 7, 31))
        self.assertEqual(r.date_next, datetime.date(2014, 9, 1)) # First day of September 2014

        self.assertEqual(r.get_subject(), u"Report for example.com (July)")

    def test_month_range(self):
        report = self._create_report_model('activity-month')
        since_time = datetime.datetime(2013, 2, 15)
        r = get_report('activity-month')(report, since_time)

        previous_date_start, date_start, date_end, date_next = r.get_date_range(since_time)
        self.assertEqual(previous_date_start, datetime.date(2012, 12, 1))
        self.assertEqual(date_start, datetime.date(2013, 1, 1))
        self.assertEqual(date_end, datetime.date(2013, 1, 31))
        self.assertEqual(date_next, datetime.date(2013, 3, 1))

    def test_sparse_cumulative(self):
        data = [
            (datetime.date(2014, 1, 1), 1),
            (datetime.date(2014, 1, 5), 2),
            (datetime.date(2014, 2, 1), 3),
            (datetime.date(2014, 2, 2), 4),
            (datetime.date(2014, 2, 2), 5),
        ]

        iterable = data[:1]
        monthly_data, max_value = sparse_cumulative(iterable)
        self.assertEqual(monthly_data, [[1]])
        self.assertEqual(max_value, 1)

        iterable = data[:1] * 3
        monthly_data, max_value = sparse_cumulative(iterable)
        self.assertEqual(monthly_data, [[3]])
        self.assertEqual(max_value, 3)

        monthly_data, max_value = sparse_cumulative(data[:1], final_date=datetime.date(2014, 1, 5))
        self.assertEqual(monthly_data, [[1, 1, 1, 1, 1]])
        self.assertEqual(max_value, 1)

        monthly_data, max_value = sparse_cumulative(data)
        last_month, current_month = monthly_data
        self.assertEqual(max_value, 12)
        self.assertEqual(len(last_month), 30)
        self.assertEqual(len(current_month), 2)

        self.assertEqual(last_month, [1, 1, 1, 1, 3] + [3] * 25)
        self.assertEqual(current_month, [3, 12])

    def test_quarter(self):
        data = [
            (datetime.date(2014, 1, 1), 1),
            (datetime.date(2014, 2, 1), 1),
            (datetime.date(2014, 3, 31), 1),
            (datetime.date(2014, 4, 1), 2),
            (datetime.date(2014, 5, 31), 2),
            (datetime.date(2014, 6, 1), 2),
            (datetime.date(2014, 6, 30), 2),
            (datetime.date(2014, 7, 1), 3),
            (datetime.date(2014, 8, 1), 3),
            (datetime.date(2014, 9, 30), 3),
            (datetime.date(2014, 10, 1), 4),
            (datetime.date(2014, 12, 31), 4),
        ]

        for d, q in data:
            self.assertEqual(q, date_to_quarter(d))
            start, end = quarter_to_dates(q, year=2014)
            self.assertEqual(q, date_to_quarter(start))
            self.assertEqual(q, date_to_quarter(end))
            self.assertTrue(start <= d <= end)

