<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

    <section id="credit-card">
    % if c.user.stripe_customer_id:
        <h2>Credit Card: ✓</h2>

        <form action="${request.route_path('api')}" method="post" onsubmit="return confirm('Are you sure you want to cancel your subscription? Reports will be suspended until you add another credit card.');">
            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="settings.payments_cancel" />
            <input type="hidden" name="format" value="redirect" />

            <p>
                <input type="submit" class="negative" value="Remove Credit Card" />
            </p>
        </form>

        % if c.user.num_remaining:
        <p>
            You will be charged $8/month only when your free emails run out.
        </p>
        % endif

    % else:
        <h2>Add a credit card</h2>

        <p>
            You will be charged $8/month only when your free emails run out.
        </p>

        ${forms.payment_form()}
    % endif
    </section>

    <section id="delete">
        <h2>Account</h2>

        <ul>
            <li><a href="${request.route_path('account_delete')}">Cancel subscription &amp; delete account</a> (cannot be undone)
        </ul>
    </section>
</div>

<%block name="tail">
<script src="//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

${h.javascript_link(request, 'briefmetrics.web:static/js/core.js')}

<script type="text/javascript" src="https://js.stripe.com/v2/"></script>
<script type="text/javascript">
    Stripe.setPublishableKey('${settings["stripe.public_key"]}');
</script>
</%block>
