<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

    <section id="credit-card">
    % if c.user.stripe_customer_id:
        <h2>Plan</h2>

        <p>
            <strong>${c.user.plan.option_str}</strong>
        </p>

        % if c.user.num_remaining:
        <p>
            You have ${c.user.num_remaining} free emails remaining. Your credit card will be charged only when your free emails run out.
        </p>
        % endif

        <form action="${request.route_path('api')}" method="post" onsubmit="return confirm('Are you sure you want to cancel your subscription? Reports will be suspended until you add another credit card.');">
            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="settings.payments_cancel" />
            <input type="hidden" name="format" value="redirect" />

            <p>
                <input type="submit" class="negative" value="Cancel Subscription" />
            </p>
        </form>

    % else:
        <h2>Add a credit card</h2>

        % if c.user.num_remaining:
        <p>
            You will be charged only when your free emails run out.
        </p>
        % endif

        ${forms.payment_form(plan=c.selected_plan)}
    % endif
    </section>

    <section id="delete">
        <h2>Account</h2>

        <p>
            Member of the Briefmetrics family since ${h.human_date(c.user.time_created, max_unit='year')}.
        </p>

        <form action="${request.route_path('account_delete')}">
            <input type="submit" class="negative" value="Delete Account" />
        </form>
    </section>
</div>

<%block name="tail">
<script type="text/javascript" src="https://js.stripe.com/v2/"></script>
<script type="text/javascript">
    Stripe.setPublishableKey('${settings["stripe.public_key"]}');
</script>
</%block>
