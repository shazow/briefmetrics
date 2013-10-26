<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">

    <section id="plan">
        <h2>Plan: ${c.user.plan and c.user.plan.title()}</h2>

        % if c.user.num_remaining:
        <p>
            Free reports remaining: ${c.user.num_remaining}
        </p>

        <p>
            <a href="#" onclick="$('#credit-card').slideDown(); return false;">Add a credit card</a>
            to upgrade your account and start the $8/mo subscription after
            your free reports run out. When you upgrade, your remaining free
            reports are doubled!
        </p>
        % elif c.user.num_remaining is not None:
            <a href="#" onclick="$('#credit-card').slideDown(); return false;">Add a credit card</a>
            to upgrade your account and start your $8/mo subscription for more
            reports.
        % endif
    </section>

    <section id="credit-card" style="display:none;">
    % if c.user.stripe_customer_id:
        <h2>Credit Card: ✓</h2>
    % else:
        <h2>Add a credit card</h2>

        ${forms.payment_form()}
    % endif
    </section>

    <section id="site">
        <h2>Select a site</h2>

        <form action="${request.current_route_path()}" method="post">

            <p>
                <select name="id">
                    <option value="">- Select a site</option>
                % for item in c.result['items']:
                    <%
                        subscribe_url = request.route_path(
                            'settings',
                            _query={'profile_id': item['id'], 'method': 'settings.subscribe'},
                        )
                        human_url = h.human_url(item['websiteUrl']) or item['name']
                        name = h.human_url(item['name'])
                    %>
                    <option value="${item['id']}" ${h.text_if(item['id'] in c.report_ids, 'selected="selected"')}>
                        ${human_url}
                        % if name not in ['All Web Site Data', human_url]:
                        ${name}
                        % endif
                        [${item['webPropertyId']}]
                    </option>
                % endfor
                </select>
            </p>

            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="settings.subscribe" />
            <input type="hidden" name="format" value="redirect" />
            <input type="submit" value="Save Settings" />
        </form>
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
