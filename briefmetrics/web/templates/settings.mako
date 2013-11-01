<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">

    % if c.report_ids or c.user.stripe_customer_id or c.user.num_remaining == 0:
    <section id="plan">
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
                    <a href="?method=settings.payments_cancel&csrf_token=${session.get_csrf_token()}" onclick="return confirm('Are you sure you want to cancel your Briefmetrics subscription?');">Cancel subscription</a>
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
            to upgrade your account and start your $8/mo subscription to resume reports.
        % else:
        <p>
            You are the proud owner of a free Briefmetrics account. Please enjoy responsibly. :)
        </p>
        % endif
    </section>
    % endif

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

        % if c.result:
        <form action="${request.current_route_path()}" method="post">

            <p>
            % if c.user.num_remaining == 0 and not c.user.stripe_customer_id:
                <select name="id" disabled="disabled">
                    <option>No reports remaining. Upgrade to resume.</option>
                </select>
            % else:
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
            % endif
            </p>

            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="settings.subscribe" />
            <input type="hidden" name="format" value="redirect" />
            <input type="submit" value="Save Settings" />
        </form>
        % else:
        <p>
            <strong>Briefmetrics was unable to load a list of your Google Analytics properties.</strong> Are you sure you signed in with the correct Google account? 
        </p>
        <p>
            You can delete this account below and try signing in again with a different account.
        </p>
        <p>
            If you don't have any Google Analytics accounts, then Briefmetrics won't be useful for you yet. :)
        </p>
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
