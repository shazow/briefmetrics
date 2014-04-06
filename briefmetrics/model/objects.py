import datetime
import logging

from unstdlib import random_string, now
from sqlalchemy import orm, types
from sqlalchemy import Column, ForeignKey, Index

from briefmetrics.lib import pricing
from . import meta, _types


__all__ = [
    'User',
    'Account',
    'Report',
    'ReportLog',
    'Subscription',
]


log = logging.getLogger(__name__)

# FIXME: Cascades are broken in dev.


class User(meta.Model): # Email address / login
    __tablename__ = 'user'
    __json_whitelist__ = ['id', 'email']

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    email = Column(types.Unicode, nullable=False, index=True, unique=True)
    email_token = Column(types.String, default=lambda: random_string(16), nullable=False)

    display_name = Column(types.Unicode)

    is_verified = Column(types.Boolean, default=False, nullable=False)
    time_verified = Column(types.DateTime)

    is_subscribed = Column(types.Boolean, default=True, nullable=False)
    time_subscribed = Column(types.DateTime)

    is_admin = Column(types.Boolean, default=False, nullable=False)
    invited_by_user_id = Column(types.Integer)

    plan_id = Column(types.String)
    num_remaining = Column(types.Integer)

    stripe_customer_id = Column(types.String)

    config = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # Whitelabel settings
    ''' Example config:
        {
            "email_header_image": "delappdesign.gif",
            "reply_to": "support@delappdesign.com",
            "from_link": "http://www.delappdesign.com/",
            "from_name": "DeLapp Design",
            "style_a_color": "#7688c9",
            "style_permalink_color": "#7688c9",
            "style_thead_background": "#eeeeee"
        }
    '''

    @property
    def unsubscribe_token(self):
        return '%s-%s' % (self.email_token, self.id)

    def set_plan(self, plan_id):
        plan = pricing.PLANS_LOOKUP[plan_id]
        self.plan_id = plan_id

        num_remaining = plan.features.get('num_emails')
        if not num_remaining and self.num_remaining:
            pass
        else:
            self.num_remaining = num_remaining

    @property
    def plan(self):
        return pricing.PLANS_LOOKUP[self.plan_id or 'trial']

    @property
    def email_to(self):
        if self.display_name:
            return u'"{display_name}" <{email}>'.format(
                display_name=self.display_name.replace('"', '&#34;'),
                email=self.email,
            )

        return self.email


class Account(meta.Model): # OAuth Service Account (such as Google Analytics)
    __tablename__ = 'account'
    __json_whitelist__ = ['id', 'user_id', 'display_name']

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    display_name = Column(types.Unicode)
    oauth_token = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict)

    # Owner
    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE'), index=True)
    user = orm.relationship(User, innerjoin=True, backref=orm.backref('account', cascade='all,delete', uselist=False))


class Report(meta.Model): # Property within an account (such as a website)
    __tablename__ = 'report'
    __json_whitelist__ = ['id', 'time_next', 'account_id', 'display_name', 'type']

    TYPES = [
        ('day', 'Alerts (Daily)'),
        ('week', 'Weekly'), # TODO: Activity (Weekly)?
        ('month', 'Trends (Monthly)'),
        ('activity-month', 'Activity (Monthly)'),
       #'quarter',
       #'combine',
       #'alert',
    ]

    DEFAULT_TYPE = 'week'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    time_last = Column(types.DateTime)
    time_next = Column(types.DateTime, index=True)

    # Owner
    account_id = Column(types.Integer, ForeignKey(Account.id, ondelete='CASCADE'), index=True)
    account = orm.relationship(Account, innerjoin=True, backref=orm.backref('reports', cascade='all,delete'))

    display_name = Column(types.Unicode)
    remote_data = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # WebPropertyId, ProfileId, etc.
    remote_id = Column(types.String)
    config = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # Display settings

    users = orm.relationship(User, innerjoin=True, secondary='subscription', backref='reports')

    # FIXME: Use croniter?
    time_preferred = Column(types.DateTime) # Granularity relative to type
    type = Column(_types.Enum(TYPES), default='week')

    @property
    def type_label(self):
        return self.__table__.columns['type'].type.name_labels[self.type]

    def next_preferred(self, now):
        # Add preferred time offset
        # TODO: Use combine?
        # TODO: Use delorean/arrow? :/
        time_preferred = self.time_preferred or self.encode_preferred_time()
        datetime_tuple = now.timetuple()[:3] + time_preferred.timetuple()[3:6]
        now = datetime.datetime(*datetime_tuple)
        days_offset = 1

        if self.type == 'week':
            preferred_weekday = time_preferred.weekday() if time_preferred.day > 1 else 0
            days_offset = preferred_weekday - now.weekday()
            if days_offset < 0:
                days_offset += 7

        if self.type == 'month':
            next_month = now + datetime.timedelta(days=32-now.day)
            next_month = next_month.replace(day=1)

            if time_preferred.day != 1:
                weekday_offset = time_preferred.weekday() - next_month.weekday()
                if weekday_offset:
                    next_month += datetime.timedelta(days=7 + weekday_offset)

            days_offset = (next_month - now).days

        return now + datetime.timedelta(days=days_offset)

    @staticmethod
    def encode_preferred_time(hour=13, minute=0, second=0, weekday=None, min_year=1900):
        """
        ...

        :param weekday:
            Monday == 0 ... Sunday == 6
        """
        d = datetime.datetime(min_year, 1, 1).replace(hour=hour, minute=minute, second=second)
        if weekday is not None:
            d += datetime.timedelta(days=7 - d.weekday() + weekday)
        return d

    def set_time_preferred(self, **kw):
        self.time_preferred = self.encode_preferred_time(**kw)


class ReportLog(meta.Model):
    __tablename__ = 'report_log'
    __json_whitelist__ = ['id', 'time_sent', 'report_id', 'display_name', 'subject']

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_sent = Column(types.DateTime)

    seconds_elapsed = Column(types.Float)
    num_recipients = Column(types.Integer)
    # TODO: num_google_queries
    # TODO: num_db_queries

    # Owner
    account_id = Column(types.Integer, ForeignKey(Account.id, ondelete='CASCADE'), index=True)
    account = orm.relationship(Account, innerjoin=True, backref=orm.backref('report_logs', cascade='all,delete'))

    display_name = Column(types.Unicode)
    report_id = Column(types.Integer) # Unbounded
    type = Column(_types.Enum(Report.TYPES))

    remote_id = Column(types.String)
    subject = Column(types.Unicode)
    body = Column(types.UnicodeText)

    access_token = Column(types.String, default=lambda: random_string(16))

    @classmethod
    def create_from_report(cls, report, body, subject, seconds_elapsed=None, time_sent=None):
        report_log = cls.create(
            seconds_elapsed=seconds_elapsed,
            account_id=report.account_id,
            display_name=report.display_name,
            report_id=report.id,
            type=report.type,
            remote_id=report.remote_id,
            subject=subject,
            body=body,
            time_sent=time_sent,
        )

        return report_log


class Subscription(meta.Model): # Subscription to a report
    __tablename__ = 'subscription'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE')) # TODO: index=true
    user = orm.relationship(User, innerjoin=True, backref=orm.backref('subscriptions', cascade='all,delete'))

    report_id = Column(types.Integer, ForeignKey(Report.id, ondelete='CASCADE'), index=True)
    report = orm.relationship(Report, innerjoin=True, backref=orm.backref('subscriptions', cascade='all,delete'))


'''
class Notification(meta.Model):
    __tablename__ = 'notification'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    time_show = Column(types.DateTime, default=now, nullable=False)
    time_expire = Column(types.DateTime)
    time_dismissed = Column(types.DateTime)

    is_private = Column(types.Boolean, default=True, nullable=False)

    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE'))
    user = orm.relationship(User, innerjoin=True, backref=orm.backref('notifications', cascade='all,delete'))

    report_id = Column(types.Integer, ForeignKey(Report.id, ondelete='CASCADE'))
    report = orm.relationship(Report, backref=orm.backref('notifications', cascade='all,delete'))

    queue = Column(types.String)
    body = Column(types.Unicode)

Index('ix_notification_time',
      Notification.user_id,
      Notification.time_dismissed.desc(),
      Notification.time_show,
)
'''
