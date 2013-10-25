import logging

from unstdlib import random_string, now
from sqlalchemy import orm, types
from sqlalchemy import Column, ForeignKey

from . import meta, _types


__all__ = [
    'User',
    'Account',
    'Report',
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

    is_verified = Column(types.Boolean, default=False, nullable=False)
    time_verified = Column(types.DateTime)

    is_subscribed = Column(types.Boolean, default=True, nullable=False)
    time_subscribed = Column(types.DateTime)

    is_admin = Column(types.Boolean, default=False, nullable=False)
    invited_by_user_id = Column(types.Integer)

    plan = Column(types.String, default='tester')
    num_remaining = Column(types.Integer)

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
    __json_whitelist__ = ['id', 'time_next', 'account_id', 'display_name']

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

    # TODO: Add type (daily, weekly, monthly)


class Subscription(meta.Model): # Subscription to a report
    __tablename__ = 'subscription'

    id = Column(types.Integer, primary_key=True)
    time_created = Column(types.DateTime, default=now, nullable=False)
    time_updated = Column(types.DateTime, onupdate=now)

    user_id = Column(types.Integer, ForeignKey(User.id, ondelete='CASCADE')) # TODO: index=true
    user = orm.relationship(User, innerjoin=True)

    report_id = Column(types.Integer, ForeignKey(Report.id, ondelete='CASCADE'), index=True)
    report = orm.relationship(Report, innerjoin=True)
