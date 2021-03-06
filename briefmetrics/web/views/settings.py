import logging
from unstdlib import get_many

from briefmetrics import api, model
from briefmetrics.lib.exceptions import APIControllerError, LoginRequired
from briefmetrics.lib.image import save_logo
from briefmetrics.lib.service import registry as service_registry

from .api import expose_api, handle_api
from briefmetrics.lib.controller import Controller
from briefmetrics.lib.pricing import PLAN_DEFAULT


log = logging.getLogger(__name__)


@expose_api('settings.payments_set')
def settings_payments(request):
    user = api.account.get_user(request, required=True)
    stripe_token, plan_id, ga_cid = get_many(request.params, optional=['stripe_token', 'plan_id', 'ga_cid'])

    payment_type = 'stripe'
    if user.payment and user.payment.id == 'namecheap':
        payment_type = 'namecheap'
    elif not stripe_token and not request.registry.settings.get('testing'):
        raise APIControllerError('Missing Stripe card token.')

    metadata = {}
    if ga_cid:
        metadata['ga_cid'] = ga_cid

    subject = 'Payment added: [%s] %s'
    if user.payment:
        subject = 'Payment updated: [%s] %s'

    api.account.set_payments(user, plan_id=plan_id, card_token=stripe_token, metadata=metadata, payment_type=payment_type)
    api.email.notify_admin(request, subject % (user.id, user.display_name), 'plan_id=%s' % user.plan_id)

    request.flash('Payment information is set.')


@expose_api('settings.payments_cancel')
def settings_payments_cancel(request):
    user = api.account.get_user(request, required=True)
    plan_id = user.plan_id
    api.account.delete_payments(user)

    api.email.notify_admin(request, 'Payment removed: [%s] %s' % (user.id, user.display_name), 'original plan_id=%s' % plan_id)

    request.flash('Subscription cancelled.')


@expose_api('settings.plan')
def settings_plan(request):
    plan_id, format = get_many(request.params, ['plan_id'], optional=['format'])
    user = api.account.get_user(request)

    if not user:
        if format == 'redirect':
            request.session['plan_id'] = plan_id
            request.session.save()

        raise LoginRequired(next=request.route_path('settings'))

    if plan_id == 'enterprise':
        api.email.notify_admin(request, 'Enterprise plan inquery: [%s] %s' % (user.id, user.display_name), user.email_to)
        request.flash('The Enterprise plan is only available in limited access at the moment. We will reach out to you when a slot becomes available. You are welcome to choose another plan for now.')
        return

    old_plan_id = user.plan_id
    api.account.set_plan(user, plan_id=plan_id)
    request.flash('Plan updated.')

    api.email.notify_admin(request, 'Plan changed: [%s] %s' % (user.id, user.display_name), '%s -> %s' % (old_plan_id, user.plan_id))


@expose_api('settings.branding')
def settings_branding(request):
    user = api.account.get_user(request, required=True)
    header_logo, header_text, from_name, reply_to = get_many(request.params, optional=['header_logo', 'header_text', 'from_name', 'reply_to'])

    if not user.get_feature('custom_branding'):
        raise APIControllerError('Your plan does not include custom branding. Please upgrade your plan.')

    if reply_to and '@' not in reply_to:
        raise APIControllerError('"Reply To" field must be a valid email address.')

    base_dir = request.features.get('upload_logo')
    if base_dir and hasattr(header_logo, 'file'):
        prefix = '%s-' % user.id

        try:
            user.config['email_header_image'] = save_logo(
                fp=header_logo.file,
                base_dir=base_dir,
                replace_path=user.config.get('email_header_image'),
                prefix=prefix,
                pretend=request.registry.settings.get('testing'),
            )
        except (ValueError, OSError) as e:
            log.error('settings.branding: Failed to save logo: %r' % e)
            raise APIControllerError("Failed to read image '%s'. Please re-save the image as a PNG and try again." % header_logo.filename)

    user.config['email_intro_text'] = header_text
    user.config['reply_to'] = reply_to
    user.config['from_name'] = from_name

    model.Session.commit()

    request.flash('Branding updated.')


@expose_api('settings.feedback')
def settings_feedback(request):
    user = api.account.get_user(request, required=True)
    body, subject, extend_trial = get_many(request.params, optional=['body', 'subject', 'extend_trial'])

    text = "From user_id=%s:\n%s\n%s\n\n===\n\n%s" % (user.id, user.email_to, " [extend_trial=%d]" % user.num_remaining if extend_trial else "", body)
    api.email.notify_admin(request, subject, text=text)
    request.flash('Feedback submitted. We\'ll be in touch shortly!')


class SettingsController(Controller):

    @handle_api(['settings.payments_set', 'settings.payments_cancel', 'settings.plan', 'settings.branding'])
    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='accounts')

        plan_id = self.request.session.pop('plan_id', None)
        if plan_id:
            api.account.set_plan(user, plan_id=plan_id)
            self.request.flash('Plan updated.')

        self.c.selected_plan = user.plan if user.plan.id != 'trial' else PLAN_DEFAULT
        self.c.user = user

        available_services = set(['google', 'stripe'])
        for a in user.accounts:
            available_services.discard(a.service)

        # TODO: Merge with plan level/features?
        self.c.extra_services = get_many(service_registry, available_services)

        return self._render('settings.mako')
