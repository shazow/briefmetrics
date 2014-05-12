import stripe
import logging

from briefmetrics import model
from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError, LoginRequired
from briefmetrics.lib import pricing
from briefmetrics.web.environment import httpexceptions

from sqlalchemy import orm
from unstdlib import iterate, get_many

from . import google as api_google


log = logging.getLogger(__name__)


# Request helpers

def get_user_id(request, required=False):
    """
    Get the current logged in user_id, else None.

    If required, then redirect to login page while preserving the current destination.
    """
    user_id = request.session.get('user_id')
    if user_id:
        return user_id

    if not required:
        return

    raise LoginRequired(next=request.path_qs)


def get_user(request, required=False, joinedload=None):
    """
    Get the current logged in User object, else None.
    """
    user_id = get_user_id(request, required=required)
    if not user_id:
        return

    q = Session.query(model.User)
    for p in iterate(joinedload or []):
        q = q.options(orm.joinedload_all(p))

    u = q.get(user_id)
    if not u:
        request.session.pop('user_id', None)
        request.session.save()
        return get_user(request, required=required) # Try again.

    return u

def get_admin(request, required=True):
    u = get_user(request, required=required)
    if u.is_admin:
        return u
    if not required:
        return

    raise httpexceptions.HTTPForbidden()


def login_user_id(request, user_id):
    """
    Force current session to be logged in as user_id, regardless of credentials.
    """
    # Success
    request.session['user_id'] = user_id
    request.session.save()


def login_user(request):
    is_force, token, save_redirect = get_many(request.params, optional=['force', 'token', 'next'])
    user_id = get_user_id(request)

    if user_id and not is_force:
        return user_id

    if token and request.features.get('token_login'):
        # Only enabled during testing
        u = get(token=token)
        if u:
            login_user_id(request, u.id)
            return u.id

    request.session['next'] = save_redirect
    request.session.save()

    oauth = api_google.auth_session(request)
    next, state = api_google.auth_url(oauth)
    request.session['oauth_state'] = state
    raise httpexceptions.HTTPSeeOther(next)


def logout_user(request):
    """
    Delete login information from the current session. Log out any user if
    logged in.
    """
    request.session.pop('user_id', None)
    request.session.save()



# API queries


def get(id=None, email=None, token=None):
    if not any([id, email, token]):
        raise APIError('Must specify user query criteria.')

    q = Session.query(model.User)

    if id:
        q = q.filter_by(id=id)

    if email:
        q = q.filter_by(email=email)

    if token:
        email_token, id = token.split('-', 2)
        q = q.filter_by(id=int(id), email_token=email_token)

    return q.first()


def get_or_create(user_id=None, email=None, token=None, display_name=None, plan_id=None, **create_kw):
    u = None

    q = Session.query(model.User).join(model.Account)
    q = q.options(orm.contains_eager(model.User.account))

    if user_id:
        u = q.get(user_id)
        if not u:
            raise APIError('Invalid user: %s' % user_id)

    elif email:
        u = q.filter(model.User.email==email).first()

    if not u:
        u = model.User.create(email=email, display_name=display_name, **create_kw)
        u.account = model.Account.create(display_name=display_name, user=u)
        u.set_plan(plan_id or 'trial')

    if token and token.get('refresh_token'):
        # Update token if it's a better one (with refresh).
        u.account.oauth_token = token

    Session.commit()
    return u


def delete(user_id):
    # TODO: user_id -> user
    u = model.User.get(user_id)
    if not u:
        raise APIError('Invalid user: %s' % user_id)

    delete_payments(u)
    u.delete()
    Session.commit()


def set_payments(user, plan_id=None, card_token=None):
    if plan_id:
        try:
            user.set_plan(plan_id)
        except KeyError:
            raise APIError('Invalid plan: %s' % plan_id)

    if not card_token:  # For testing
        log.warn('Skipping interfacing set_payments with Stripe for user_id: %s' % user.id)
        Session.commit()
        return user

    description = 'Briefmetrics User: %s' % user.email

    if user.stripe_customer_id:
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.card = card_token
        customer.description = description
        customer.save()
    else:
        customer = stripe.Customer.create(
            card=card_token,
            description=description,
            email=user.email,
        )
        user.stripe_customer_id = customer.id

    Session.commit()
    return user


def delete_payments(user):
    if user.stripe_customer_id:
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.delete()
        user.stripe_customer_id = None

    if not user.num_remaining:
        user.num_remaining = 0

    Session.commit()


def _plan_to_stripe(plan_id):
    return 'briefmetrics_%s' % plan_id


def start_subscription(user):
    if not user.stripe_customer_id:
        raise APIError("Cannot start subscription for user without a credit card: %s" % user.id)

    customer = stripe.Customer.retrieve(user.stripe_customer_id)
    try:
        customer.update_subscription(plan=_plan_to_stripe(user.plan_id))
    except stripe.CardError as e:
        delete_payments(user)
        raise APIError('Failed to start payment plan: %s' % e.message)


def set_plan(user, plan_id, update_subscription=None):
    try:
        user.set_plan(plan_id)
        Session.commit()
    except KeyError:
        raise APIError('Invalid plan: %s' % plan_id)

    if update_subscription is None:
        # Default behaviour
        update_subscription = user.num_remaining <= 0

    if update_subscription and user.stripe_customer_id:
        start_subscription(user)


def sync_plans(pretend=True, include_hidden=False):
    local_plans = set(key for key, plan in pricing.Plan.all() if not plan.is_hidden)

    r = stripe.Plan.all()
    for plan in r.data:
        try:
            local_plan_id = plan.id.split('briefmetrics_', 1)[1]
        except IndexError, e:
            print "Invalid plan prefix: %s" % plan.id
            continue

        if local_plan_id not in local_plans:
            print "Plan missing locally: {}".format(local_plan_id)
            continue

        local_plans.remove(local_plan_id)
        local_plan = pricing.Plan.get(local_plan_id)

        if plan.amount != local_plan.price_monthly:
            print "Plan discrepency for '{id}': Remote amount {remote_amount}, local amount {local_amount}".format(
                id=plan.id,
                remote_amount=plan.amount,
                local_amount=local_plan.price_monthly,
            )

    for plan_id in local_plans:
        print "Plan missing remotely: {}".format(plan_id)
        if pretend:
            continue

        plan = pricing.Plan.get(plan_id)
        stripe.Plan.create(
            id=_plan_to_stripe(plan_id),
            amount=plan.price_monthly,
            interval='month',
            name='Briefmetrics: %s' % plan.name,
            currency='usd',
            statement_description='Briefmetrics',
        )
