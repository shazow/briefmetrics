<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">

    <section id="plan" ${h.text_if(not c.report_ids, 'style="display:none;"')}>
        <h2>Plan</h2>

        % if c.user.stripe_customer_id:
            % if c.user.num_remaining:
            <p>
                Free reports until subscription starts: <strong>${c.user.num_remaining}</strong>
            </p>
            % else:
            <p>
                $8 per month.
            </p>
            % endif
            <ul>
                <li>
                    <a href="?method=settings.payments_cancel&csrf_token=${session.get_csrf_token()}">Cancel subscription</a>
                </li>
            </ul>
        % elif c.user.num_remaining:
        <p>
            Free reports remaining: <strong>${c.user.num_remaining}</strong>
        </p>

        <ul>
            <li><a class="highlight" href="#" onclick="$('#credit-card').slideDown(); return false;">Add a credit card</a>
                to upgrade your account.</li>
            <li>$8/mo subscription starts only after your free reports run out.</li>
            <li>When you upgrade, your remaining free reports are doubled!</li>
        </ul>
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
