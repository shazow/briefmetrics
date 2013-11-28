import stripe

from briefmetrics import model
from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError, LoginRequired
from briefmetrics.lib import pricing
from briefmetrics.web.environment import httpexceptions

from sqlalchemy import orm
from unstdlib import iterate, get_many

from . import google as api_google


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
    if required:
        raise httpexceptions.HTTPForbidden()
    return


def login_user_id(request, user_id):
    """
    Force current session to be logged in as user_id, regardless of credentials.
    """
    # Success
    request.session['user_id'] = user_id
    request.session.save()


def login_user(request):
    is_force, token = get_many(request.params, optional=['force', 'token'])
    user_id = get_user_id(request)

    if user_id and not is_force:
        return user_id

    if token and request.features.get('token_login'):
        # Only enabled during testing
        u = get(token=token)
        if u:
            login_user_id(request, u.id)
            return u.id

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
    plan = pricing.PLANS_LOOKUP[plan_id or 'trial']

    q = Session.query(model.User).join(model.Account)
    q = q.options(orm.contains_eager(model.User.account))

    if user_id:
        u = q.get(user_id)
        if not u:
            raise APIError('Invalid user: %s' % user_id)

    elif email:
        u = q.filter(model.User.email==email).first()

    if not u:
        num_remaining = plan.features['num_emails']
        u = model.User.create(email=email, display_name=display_name, num_remaining=num_remaining, **create_kw)
        u.account = model.Account.create(display_name=display_name, user=u)

    if token and not (u.account.oauth_token and u.account.oauth_token.get('refresh_token')):
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


def set_payments(user, card_token, plan_id='personal'):
    plan = pricing.PLANS_LOOKUP.get(plan_id)
    if not plan:
        raise APIError('Invalid plan: %s' % plan_id)

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

    # Plan-related stuff.
    if not user.plan_id and user.num_remaining:
        user.num_remaining *= 2

    user.plan_id = plan_id

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


def start_subscription(user, plan_id=None):
    if not user.stripe_customer_id:
        raise APIError("Cannot start subscription for user without a credit card: %s" % user.id)

    plan = pricing.PLANS_LOOKUP.get(plan_id or user.plan_id)
    if plan_id and not plan:
        raise APIError('Invalid plan: %s' % plan_id)

    elif plan_id:
        user.plan_id = plan_id
        Session.commit()

    if not plan:
        raise APIError("Invalid plan: %s" % user.plan_id)

    customer = stripe.Customer.retrieve(user.stripe_customer_id)
    customer.update_subscription(plan="briefmetrics_%s" % user.plan_id)
