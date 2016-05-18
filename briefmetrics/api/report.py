import time
import logging
import datetime
import random

from sqlalchemy import orm
from unstdlib import now, get_many
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from briefmetrics.lib.controller import Context
from briefmetrics.lib.report import get_report, EmptyReportError
from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib import helpers as h
from briefmetrics import model

from . import email as api_email, account as api_account

log = logging.getLogger(__name__)

def create(account_id, remote_data=None, remote_id=None, display_name=None, subscribe_user_id=None, type=None, config=None):
    remote_id = remote_id or str(remote_data['id'])
    type = type or 'week'

    report = model.Report.get_or_create(account_id=account_id, remote_id=remote_id, type=type)
    if report.id:
        raise APIError("Report already exists.")

    report.remote_id = remote_id
    if remote_data:
        report.remote_data = remote_data
        # FIXME: This is duplicated in briefmetrics.lib.service.google.helpers
        report.display_name = h.human_url(remote_data.get('displayName') or h.human_url(remote_data.get('websiteUrl')) or remote_data.get('display_name') or remote_data.get('name'))

    if display_name:
        report.display_name = display_name

    if config:
        report.config = config

    if subscribe_user_id:
        model.Subscription.create(user_id=subscribe_user_id, report=report)

    model.Session.commit()
    return report


def combine(report_ids, is_replace=False, account_id=None, subscribe_user_id=None):
    ids_str = ','.join(map(str, report_ids))

    q = model.Session.query(model.Report).filter(model.Report.id.in_(report_ids))
    q = q.options(orm.joinedload('subscriptions'))
    reports = q.all()

    if len(reports) != len(report_ids):
        raise APIError('Not all reports exist: %s' % ids_str)

    if account_id and not all(r.account_id for r in reports):
        raise APIError('Reports do not belong to account: %s' % account_id)
    elif len(set(r.account_id for r in reports)) > 1:
        raise APIError('Inconsistent accounts for reports: %s' % ids_str)

    if not all(r.type == 'week' for r in reports):
        raise APIError('Unsupported combine type for reports: %s' % ids_str)

    remote_data = {'combined': [r.remote_data for r in reports]}
    display_name = ', '.join(r.display_name for r in reports)

    # Find common subscribers
    subscribe_user_ids = []
    if subscribe_user_id:
        subscribe_user_ids.append(subscribe_user_id)
    else:
        subscriptions = [set(s.user_id for s in subs) for subs in (r.subscriptions for r in reports)]
        subscribe_user_ids = reduce(set.intersection, subscriptions)

    report = create(
        account_id=reports[0].account_id,
        remote_data=remote_data,
        remote_id=ids_str,
        display_name=display_name,
        type='week-concat',
    )

    for subscribe_user_id in subscribe_user_ids:
        model.Subscription.create(user_id=subscribe_user_id, report=report)

    if is_replace:
        for r in reports:
            model.Session.delete(r)

    model.Session.commit()
    return report


def add_subscriber(report_id, email, display_name, invited_by_user_id=None):
    u = api_account.get_or_create(
        email=email, plan_id='recipient', service=None,
        display_name=display_name, invited_by_user_id=invited_by_user_id,
    )
    model.Subscription.get_or_create(user=u, report_id=report_id)
    model.Session.commit()

    return u


def reschedule(report_id, hour=13, minute=0, second=0, weekday=None):
    r = model.Report.get(report_id)
    if not r:
        raise APIError('report does not exist: %s' % report_id)

    ReportCls = get_report(r.type)
    since = now()
    ctx = ReportCls(r, since, None)

    r.set_time_preferred(hour=hour, minute=minute, second=second, weekday=weekday)
    r.time_next = ctx.next_preferred(since)


def get_pending(since_time=None, max_num=None, include_new=True):
    since_time = since_time or now()

    f = (model.Report.time_next <= since_time)
    if include_new:
        f |= (model.Report.time_next == None)

    q = model.Session.query(model.Report).filter(f)
    if max_num:
        q = q.limit(max_num)

    return q


# Reporting tasks:

def fetch(request, report, since_time, api_query=None, service='google', config=None):
    if not api_query:
        api_query = api_account.query_service(request, account=report.account)

    ReportCls = get_report(report.type)
    r = ReportCls(report, since_time, config=config)

    try:
        r.fetch(api_query)
    except EmptyReportError:
        r.tables = {}
        return r

    r.build()

    return r


def check_trial(request, report, has_data=True, pretend=False):
    messages = []
    force_debug = False

    owner = report.account.user
    if owner.num_remaining is None or owner.num_remaining > 1:
        return messages, force_debug

    if not owner.payment:
        messages.append(h.literal('''
            <strong>This is your final report. </strong><br />
            Please <a href="https://briefmetrics.com/settings">add a credit card now</a> to continue receiving Briefmetrics reports.
        '''.strip()))

        return messages, force_debug

    try:
        # Create subscription for customer
        api_account.start_subscription(owner)
        owner.num_remaining = None
    except APIError as e:
        force_debug = True
        messages.append(h.literal('''
            <strong>{message}</strong><br />
            Please visit <a href="https://briefmetrics.com/settings">briefmetrics.com/settings</a> to add a new credit card and resume your reports.
        '''.strip().format(message=e.message)))

    return messages, force_debug


def send(request, report, since_time=None, pretend=False, session=model.Session):
    t = time.time()

    since_time = since_time or now()

    if not pretend and report.time_next and report.time_next > since_time:
        log.warn('send too early, skipping for report: %s' % report.id)
        return

    owner = report.account.user
    if not pretend and report.time_expire and report.time_expire < since_time:
        if owner.num_remaining is None:
            # Started paying, un-expire.
            report.time_expire = None
        else:
            log.info('Deleting expired report for %s: %s' % (owner, report))
            session.delete(report)
            session.commit()
            return

    send_users = report.users
    if not send_users:
        log.warn('No recipients, skipping report: %s' % report.id)
        return

    try:
        report_context = fetch(request, report, since_time)
    except InvalidGrantError:
        subject = u"Problem with your Briefmetrics"
        html = api_email.render(request, 'email/error_auth.mako', Context({
            'report': report,
        }))

        message = api_email.create_message(request,
            to_email=owner.email,
            subject=subject,
            html=html,
        )

        if not pretend:
            api_email.send_message(request, message)
            report.delete()
            session.commit()

        log.warn('Invalid token, removed report: %s' % report)
        return
    except APIError as e:
        if not 'User does not have sufficient permissions for this profile' in e.message:
            raise

        subject = u"Problem with your Briefmetrics"
        html = api_email.render(request, 'email/error_permission.mako', Context({
            'report': report,
        }))

        message = api_email.create_message(request,
            to_email=owner.email,
            subject=subject,
            html=html,
        )

        if not pretend:
            api_email.send_message(request, message)
            report.delete()
            model.Session.commit()

        log.warn('Lost permission to profile, removed report: %s' % report)
        return


    messages, force_debug = check_trial(request, report, has_data=report_context.data, pretend=pretend)

    report_context.messages += messages
    subject = report_context.get_subject()
    template = report_context.template

    time_revive = None
    if not report_context.data:
        send_users = [report.account.user]
        template = 'email/error_empty.mako'
        time_revive = report_context.next_preferred(report_context.date_end + datetime.timedelta(days=30))

    log.info('Sending report to [%d] subscribers: %s' % (len(send_users), report))

    debug_sample = float(request.registry.settings.get('mail.debug_sample', 1))
    debug_bcc = not report.time_next or random.random() < debug_sample
    if force_debug:
        debug_bcc = True

    email_kw = {}
    from_name, from_email, reply_to, api_mandrill_key, api_mailgun_key = get_many(owner.config, optional=['from_name', 'from_email', 'reply_to', 'api_mandrill_key', 'api_mailgun_key'])
    if from_name:
        email_kw['from_name'] = from_name
    if from_email:
        email_kw['from_email'] = from_email
    if reply_to and reply_to != from_email:
        email_kw['reply_to'] = reply_to

    send_kw = {}
    if api_mandrill_key:
        send_kw['settings'] = {
            'api.mandrill.key': api_mandrill_key,
        }
        email_kw['mailer'] = 'mandrill'
    if api_mailgun_key:
        send_kw['settings'] = {
            'api.mailgun.key': api_mailgun_key,
        }
        email_kw['mailer'] = 'mailgun'

    for user in report.users:
        html = api_email.render(request, template, Context({
            'user': user,
            'report': report_context,
        }))

        message = api_email.create_message(request,
            to_email=user.email,
            subject=subject, 
            html=html,
            debug_bcc=debug_bcc,
            **email_kw
        )

        if pretend:
            continue

        api_email.send_message(request, message, **send_kw)

    model.ReportLog.create_from_report(report,
        body=html,
        subject=subject,
        seconds_elapsed=time.time()-t,
        time_sent=None if pretend else now(),
    )

    if pretend:
        session.commit()
        return

    if report_context.data:
        if owner.num_remaining == 1:
            subject = u"Your Briefmetrics trial is over"
            html = api_email.render(request, 'email/error_trial_end.mako')
            message = api_email.create_message(request,
                to_email=owner.email,
                subject=subject,
                html=html,
            )
            log.info('Sending trial expiration: %s' % owner)
            if not pretend:
                api_email.send_message(request, message)

        if owner.num_remaining:
            owner.num_remaining -= 1

    report.time_last = now()
    report.time_next = time_revive or report_context.next_preferred(report_context.date_end + datetime.timedelta(days=7)) # XXX: Generalize

    if owner.num_remaining == 0:
        report.time_expire = report.time_next

    session.commit()
