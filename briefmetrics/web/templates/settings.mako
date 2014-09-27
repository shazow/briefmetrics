<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

    <section id="credit-card">
    % if c.user.stripe_customer_id:
        <h2>Plan</h2>

        <p>
            <strong>${c.user.plan.name}</strong> at ${c.user.plan.price_str}.
            <a href="${request.route_path('pricing')}" class="button">Change Plan</a>
            <a class="button" href="#update-payment" onclick="$('#update-payment').show(); return false;">Update Credit Card</a>
        </p>

        % if c.selected_plan.in_group:
            ${forms.pricing_plan_group(c.selected_plan.in_group, c.selected_plan.id)}
        % endif

        % if c.user.num_remaining:
        <p>
            You have ${c.user.num_remaining} free emails remaining. Your credit card will be charged only when your free emails run out.
        </p>
        % endif

        <div id="update-payment" class="hidden">
            <h3>Update credit card</h3>

            ${forms.payment_form()}
        </div>

    % else:
        <h2>Add a credit card</h2>

        % if c.user.num_remaining:
        <p>
            You will be charged only when your free emails run out.
        </p>
        % endif

        ${forms.payment_form(plan=c.selected_plan)}

        % if c.selected_plan.in_group:
            ${forms.pricing_plan_group(c.selected_plan.in_group, c.selected_plan.id)}
        % endif
    % endif
    </section>

    <section id="branding">
        <h2>Custom Branding</h2>

        % if not c.user.get_feature('custom_branding'):
            <p>Configure your emails to look consistent with your company.
                <a href="${request.route_path('pricing')}">Upgrade your plan</a> to unlock this feature.
            </p>
        % else:
            ${forms.custom_branding(c.user, enable_logo=request.features.get('upload_logo'))}
        % endif

    </section>

    % if request.features.get('connected_services'):
    <section id="connections">
        <h2>Connected Services</h2>

        ${forms.account_connections(c.user, extra_services=c.extra_services)}
    </section>
    % endif

    <section id="delete">
        <h2>Account</h2>

        <p>
            Member of the Briefmetrics family since ${h.human_date(c.user.time_created, max_unit='year')}.
        </p>

        % if c.user.stripe_customer_id:
            ${forms.payment_cancel()}
        % endif

        <form action="${request.route_path('account_delete')}">
            <input type="submit" class="negative" value="Delete Account" />
            <span class="button-note">Remove all of your information from our servers.</span>
        </form>
    </section>
</div>

<%block name="tail">
<script type="text/javascript" src="https://js.stripe.com/v2/"></script>
<script type="text/javascript">
    Stripe.setPublishableKey('${settings["api.stripe.public_key"]}');
</script>
</%block>
