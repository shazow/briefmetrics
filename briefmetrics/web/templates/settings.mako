<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

    <section id="credit-card">
    % if c.user.stripe_customer_id:
        <h2>Credit Card: ✓</h2>
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
