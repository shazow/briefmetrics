import datetime
import logging

from unstdlib import random_string, now
from sqlalchemy import orm, types
from sqlalchemy import Column, ForeignKey

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

    plan = Column(types.String)
    num_remaining = Column(types.Integer)

    stripe_customer_id = Column(types.String)

    @property
    def unsubscribe_token(self):
        return '%s-%s' % (self.email_token, self.id)


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
    user = orm.relationship(User, innerjoin=True, backref=orm.backref('account', uselist=False))


class Report(meta.Model): # Property within an account (such as a website)
    __tablename__ = 'report'
    __json_whitelist__ = ['id', 'time_next', 'account_id', 'display_name', 'type']

    TYPES = [
        'day',
        'week',
        'month',
       #'quarter',
       #'combine',
       #'alert',
    ]

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    time_last = Column(types.DateTime)
    time_next = Column(types.DateTime, index=True)

    # Owner
    account_id = Column(types.Integer, ForeignKey(Account.id, ondelete='CASCADE'), index=True)
    account = orm.relationship(Account, innerjoin=True, backref='reports')

    display_name = Column(types.Unicode)
    remote_data = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # WebPropertyId, ProfileId, etc.
    remote_id = Column(types.String)

    users = orm.relationship(User, innerjoin=True, secondary='subscription', backref='reports')

    # FIXME: Use croniter?
    time_preferred = Column(types.DateTime) # Granularity relative to type
    type = Column(_types.Enum(TYPES), default='week')

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
                next_month += time_preferred.weekday()

            days_offset = (next_month - now).days

        return now + datetime.timedelta(days=days_offset)

    @staticmethod
    def encode_preferred_time(hour=13, minute=0, second=0, weekday=None, min_year=1900):
        d = datetime.datetime(min_year, 1, 1).replace(hour=hour, minute=minute, second=second)
        if weekday is not None:
            d += datetime.timedelta(days=7 - d.weekday() + weekday)
        return d

    def set_time_preferred(self, **kw):
        self.time_preferred = self.encode_preferred_time(**kw)


class ReportLog(meta.Model):
    __tablename__ = 'report_log'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)

    seconds_elapsed = Column(types.Float)
    num_recipients = Column(types.Integer)
    # TODO: num_google_queries
    # TODO: num_db_queries

    # Owner
    account_id = Column(types.Integer, ForeignKey(Account.id, ondelete='CASCADE'), index=True)
    account = orm.relationship(Account, innerjoin=True, backref='report_logs')

    display_name = Column(types.Unicode)
    report_id = Column(types.Integer) # Unbounded
    type = Column(_types.Enum(Report.TYPES))

    remote_id = Column(types.String)
    subject = Column(types.Unicode)
    body = Column(types.UnicodeText)

    access_token = Column(types.String, default=lambda: random_string(16))

    @classmethod
    def create_from_report(cls, report, body, subject, seconds_elapsed=None):
        report_log = cls.create(
            seconds_elapsed=seconds_elapsed,
            account_id=report.account_id,
            display_name=report.display_name,
            report_id=report.id,
            type=report.type,
            remote_id=report.remote_id,
            subject=subject,
            body=body,
        )

        return report_log


class Subscription(meta.Model): # Subscription to a report
    __tablename__ = 'subscription'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE')) # TODO: index=true
    user = orm.relationship(User, innerjoin=True)

    report_id = Column(types.Integer, ForeignKey(Report.id, ondelete='CASCADE'), index=True)
    report = orm.relationship(Report, innerjoin=True)
