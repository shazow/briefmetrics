from briefmetrics import model
from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError, LoginRequired

from sqlalchemy import orm
from unstdlib import iterate


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


def login_user_id(request, user_id):
    """
    Force current session to be logged in as user_id, regardless of credentials.
    """
    # Success
    request.session['user_id'] = user_id
    request.session.save()


def logout_user(request):
    """
    Delete login information from the current session. Log out any user if
    logged in.
    """
    request.session.pop('user_id', None)
    request.session.save()


# API queries


def get(email=None):
    return model.User.get_by(email=email)


def get_or_create(user_id=None, email=None, token=None, display_name=None, **create_kw):
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
        u = model.User.create(email=email, **create_kw)
        u.account = model.Account.create(display_name=display_name, user=u)

    if token and not (u.account.oauth_token and u.account.oauth_token.get('refresh_token')):
        # Update token if it's a better one (with refresh).
        u.account.oauth_token = token

    Session.commit()
    return u

