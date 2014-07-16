import stripe
import logging
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, OAuth2Error

from briefmetrics import model
from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError, LoginRequired
from briefmetrics.lib import pricing
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.web.environment import httpexceptions

from sqlalchemy import orm
from unstdlib import iterate


log = logging.getLogger(__name__)



# Request helpers

def connect_user(request, oauth, user_required=False):
    user, account = get_account(request, service=oauth.id, user_required=user_required)

    code = request.params.get('code')
    if not code:
        raise httpexceptions.HTTPBadRequest('Missing code.')

    error = request.params.get('error')
    if error:
        raise APIError('Failed to connect: %s' % error)

    url = request.current_route_url().replace('http://', 'https://') # We lie, because honeybadger.

    try:
        token = oauth.auth_token(url)
    except InvalidGrantError:
        # Try again.
        raise httpexceptions.HTTPSeeOther(request.route_path('account_login', service=oauth.id))
    except OAuth2Error as e:
        raise APIError("Unexpected authentication error, please try again: %s" % e.description)

    if not user:
        # New user
        email, display_name = oauth.query_user()
        user = get_or_create(
            email=email,
            service=oauth.id,
            token=token,
            display_name=display_name,
        )
        account = user.accounts[0]
    elif not account:
        # New account
        account = model.Account.create(display_name=user.display_name, user=user, oauth_token=token, service=oauth.id)
    else:
        # Update account
        account.oauth_token = token
        has_report = Session.query(model.Report).filter_by(account_id=account.id).limit(1).count()
        if has_report:
            # Already exists, skip autocreate.
            oauth.is_autocreate = False

    Session.commit()

    return account


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

def get_account(request, service=None, account_id=None, user_required=False):
    user = get_user(request, required=user_required, joinedload=['accounts'])
    if not user:
        return None, None

    return user, user.get_account(service=service, id=account_id)

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
    request.session['user_id'] = int(user_id)
    request.session.save()


def login_user(request, service='google', save_redirect=None, token=None, is_force=None):
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

    oauth = service_registry[service or 'google'](request)
    next, state = oauth.auth_url() # is_force=is_force
    request.session['oauth_state'] = state
    raise httpexceptions.HTTPSeeOther(next)


def logout_user(request):
    """
    Delete login information from the current session. Log out any user if
    logged in.
    """
    request.session.pop('user_id', None)
    request.session.save()


def query_service(request, account):
    return service_registry[account.service](request, token=account.oauth_token).create_query(cache_keys=(account.id,))


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


def get_or_create(user_id=None, email=None, service='google', token=None, display_name=None, plan_id=None, **create_kw):
    u = None
    q = Session.query(model.User).options(orm.joinedload(model.User.accounts))

    if user_id:
        u = q.get(user_id)
        if not u:
            raise APIError('Invalid user: %s' % user_id)

    elif email:
        u = q.filter(model.User.email==email).first()

    if not u:
        u = model.User.create(email=email, display_name=display_name, **create_kw)
        set_plan(u, plan_id or 'trial')

    if service:
        # Create account
        account = u.get_account(service=service)
        if not account:
            account = model.Account.create(display_name=display_name, user=u, service=service)
            u.accounts.append(account)

        if token and token.get('refresh_token'):
            # Update token if it's a better one (with refresh).
            account.oauth_token = token

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
            set_plan(user, plan_id)
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
    plan = pricing.PLANS_LOOKUP.get(plan_id)
    if not plan:
        raise APIError('Invalid plan: %s' % plan_id)

    user.plan_id = plan_id
    num_remaining = plan.features.get('num_emails')
    if num_remaining or not user.num_remaining:
        user.num_remaining = num_remaining

    Session.commit()

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
        except IndexError, _:
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
