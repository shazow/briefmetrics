import datetime
import logging
import warnings

from unstdlib import random_string, now
from sqlalchemy import orm, types
from sqlalchemy import Column, ForeignKey, Index

from briefmetrics.lib import pricing, payment
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
    payment_token = Column(types.String)

    config = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # Whitelabel settings, features, etc.
    ''' Example config:
        {
            "email_intro_text": "foo bar",
            "email_header_image": "delappdesign.gif",
            "reply_to": "support@delappdesign.com",
            "from_link": "http://www.delappdesign.com/",
            "from_name": "DeLapp Design",
            "style_a_color": "#7688c9",
            "style_permalink_color": "#7688c9",
            "style_thead_background": "#eeeeee",
        }
    '''

    @property
    def unsubscribe_token(self):
        return '%s-%s' % (self.email_token, self.id)

    @property
    def plan(self):
        return pricing.PLANS_LOOKUP[self.plan_id or 'trial']

    @property
    def payment(self):
        if not self.payment_token and not self.stripe_customer_id:
            return

        if self.payment_token:
            key, token = self.payment_token.split(':', 1)
        else:
            # Fallback
            key, token = self.stripe_customer_id and "stripe", self.stripe_customer_id

        return payment.registry[key](self, token)

    def set_payment(self, key, token):
        self.payment_token = "%s:%s" % (key, token)

    def get_feature(self, feature_id, default=None):
        """
        Get a feature value, cascading from the per-user config to the plan's
        setting, while validating that the feature exists.
        """
        feature = pricing.Feature.get(feature_id)
        return self.config.get(feature.id, self.plan.features.get(feature.id, default))

    @property
    def email_to(self):
        if self.display_name:
            return u'"{display_name}" <{email}>'.format(
                display_name=self.display_name.replace('"', '&#34;'),
                email=self.email,
            )

        return self.email

    @property
    def is_active(self):
        return self.num_remaining != 0

    @property
    def account(self):
        warnings.warn("Deprecated use of User.account", DeprecationWarning)
        return self.get_account(service='google')

    def get_account(self, service=None, id=None):
        accounts = iter(self.accounts)
        if service:
            accounts = (a for a in accounts if a.service == service)
        if id:
            accounts = (a for a in accounts if a.id == int(id))

        return next(accounts, None)



class Account(meta.Model): # OAuth Service Account (such as Google Analytics)
    __tablename__ = 'account'
    __json_whitelist__ = ['id', 'user_id', 'display_name', 'service', 'remote_id']

    SERVICES = ['google', 'stripe', 'namecheap']

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    display_name = Column(types.Unicode)
    oauth_token = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict)

    # Owner
    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE'), index=True)
    user = orm.relationship(User, innerjoin=True, backref=orm.backref('accounts', cascade='all,delete'))

    service = Column(_types.Enum(SERVICES), default='google')
    remote_id = Column(types.String)
    remote_data = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # Profile info
    config = Column(_types.MutationDict.as_mutable(_types.JSONEncodedDict), default=dict) # Funnel settings

    time_revive = Column(types.DateTime, index=True)

    @property
    def service_api(self):
        # TODO: Get rid of this?
        from briefmetrics.lib.service import registry as service_registry
        return service_registry.get(self.service)


Index('ix_account_service_remote_id',
      Account.service,
      Account.remote_id
)


class Report(meta.Model): # Property within an account (such as a website)
    __tablename__ = 'report'
    __json_whitelist__ = ['id', 'time_next', 'account_id', 'display_name', 'type', 'remote_id']

    TYPES = [
        ('day', 'Alerts (Daily)'),
        ('week', 'Weekly'), # TODO: Activity (Weekly)?
        ('month', 'Trends (Monthly)'),
        ('activity-month', 'Activity (Monthly)'),
        ('stripe', 'Stripe'),
        ('week-concat', 'Weekly (Combined)'),
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

    time_preferred = Column(types.DateTime) # Granularity relative to type
    type = Column(_types.Enum(TYPES), default='week')

    @property
    def type_label(self):
        return self.__table__.columns['type'].type.name_labels[self.type]

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
