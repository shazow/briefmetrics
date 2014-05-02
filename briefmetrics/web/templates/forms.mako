<%def name="payment_form_body()">
    <div class="payment-errors inline-error"></div>
    <div>
        <label>
            Card Number
            <div>
                <input type="text" size="20" autocomplete="off" class="card-number" data-stripe="number" autocompletetype="cc-number" required />
            </div>
        </label>
        <label>
            CVC
            <div>
                <input type="text" size="4" autocomplete="off" class="card-cvc" data-stripe="cvc" autocomplete="off" required />
            </div>
        </label>
    </div>
    <div>
        <label>Month
            <div>
                <input type="text" size="2" class="card-date card-expiry-month" placeholder="MM" data-stripe="exp-month" autocompletetype="cc-month" required />
                <span class="card-expiry-sep">/</span>
            </div>
        </label>
        <label>Year
            <div>
                <input type="text" size="4" class="card-date card-expiry-year" placeholder="YYYY" data-stripe="exp-year" autocompletetype="cc-year" required />
            </div>
        </label>
        <label>
            <input type="submit" class="submit-button" value="Start Plan" />
        </label>
    </div>
</%def>


<%def name="payment_form(plan_id=None)">
    <form action="${request.route_path('api')}" method="post" class="payment" autocomplete="on">
        <div>
            <label>
                Plan
                <div>
                    <%
                        plans = [p for p in pricing.PLANS if not p.is_hidden or p.id == plan_id and p.price_monthly]
                    %>
                    % if len(plans) == 1:
                        <input type="hidden" name="plan_id" value="${plans[0].id}" />
                        <strong>
                            ${plans[0].option_str}
                        </strong>
                    % else:
                        <select name="plan_id">
                        % for plan in plans:
                            <option value="${plan.id}" ${h.text_if(plan_id==plan.id, 'selected')}>
                                ${plan.option_str}
                            </option>
                        % endfor
                        </select>
                    % endif
                </div>
            </label>
        </div>

        ${payment_form_body()}

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.payments_set" />
        <input type="hidden" name="format" value="redirect" />
    </form>
</%def>

<%def name="report_new(available_profiles, report_types)">
    % if not available_profiles or not available_profiles.get('items'):
        <p>
            <strong>Briefmetrics was unable to load a list of your Google Analytics properties.</strong> Are you sure you signed in with the correct Google account? 
        </p>
        <p>
            You can <a href="/account/delete">delete this account</a> and try signing in again with a different account.
        </p>
        <p>
            If you don't have any Google Analytics accounts, then Briefmetrics won't be useful for you yet. :)
        </p>
        <% return '' %>
    % endif

    <form action="${request.current_route_path()}" method="post" id="create-report">
        <p class="row">
            <select name="remote_id" data-placeholder="Choose a site">
                <option />
            % for item in available_profiles['items']:
                <%
                    human_url = h.human_url(item.get('websiteUrl')) or item['name']
                    name = h.human_url(item['name'])
                %>
                <option value="${item['id']}">
                    ${human_url}
                    % if name not in ['All Web Site Data', human_url]:
                    ${name}
                    % endif
                    [${item['webPropertyId']}]
                </option>
            % endfor
            </select>
        </p>


        <p class="row">

            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="report.create" />
            <input type="hidden" name="format" value="redirect" />
            <input type="submit" value="Create Report" />

            % if len(report_types) == 1:
                <input type="hidden" name="type" value="${report_types[0][0]}" />
            % else:
                <select name="type" style="width: auto;">
                % for id, label, is_active in report_types:
                    <option value="${id}"${h.text_if(is_active, " selected")}>${label}</option>
                % endfor
                </select>
            % endif
        </p>
    </form>
</%def>

<%def name="site_config(site, is_active=True, is_admin=False)">
    <%
        anchor = 'report-{}'.format(site.report.id)
    %>
    <div class="preview report" id="${anchor}">
        <nav>
            <h3>
                ${site.display_name}
            </h3>

            <div class="controls">
                <a class="button external" target="_blank" href="${h.ga_permalink('report/visitors-overview', site.report)}">Google Analytics</a>
            </div>
        </nav>

        <table class="details">
        % for type, report in site:
            <% 
                is_recipients_active = request.params.get('recipients') == str(report.id)
            %>
            <tr>
                <td>
                    <a href="${request.current_route_path(
                        _query=dict(report_id=report.id, method="report.delete", csrf_token=session.get_csrf_token())
                    )}" class="negative symbol button">&times;</a>

                    ${report.type_label}
                </td>
                <td>
                    % if not is_active:
                        No reports remaining.
                        <a href="/settings#credit-card" class="highlight">Upgrade to resume.</a>
                    % elif not report.time_next:
                        Next report is imminent.
                    % else:
                        Next report on
                        <span class="highlight">${h.human_date(report.time_next)}</span>.
                        ##at ${"{d:%H:%M} UTC".format(d=report.time_next)}
                    % endif
                </td>
                <td style="text-align: right;">
                % if is_active:
                    <a class="button ${h.text_if(is_recipients_active, 'active')} expand-recipients" href="${request.current_route_path(_query={'recipients': report.id}, _anchor=anchor)}">${h.format_int(len(report.subscriptions), '{} Recipient')}</a>

                    <a target="_blank" class="button" href="${request.route_path('reports_view', id=report.id)}">Last Report</a>
                % endif
                </td>
            </tr>
            % if is_recipients_active:
            <tr>
            % else:
            <tr style="display: none;">
            % endif
                <td colspan="3">
                    <ul class="vertical recipients">
                        % for sub in report.subscriptions:
                        <li>

                            <a href="${request.route_path('api',
                                _query=dict(
                                    subscription_id=sub.id,
                                    method='subscription.delete',
                                    csrf_token=session.get_csrf_token(),
                                    format='redirect',
                                )
                            )}" class="negative symbol button">&times;</a>
                            ${sub.user.email_to}
                        </li>
                        % endfor
                        <li>
                            ${subscription_create(report_id=report.id)}
                        </li>
                    </ul>
                </td>
            </tr>
        % endfor
        </table>
    </div>
</%def>

<%def name="subscription_create(report_id)">
    <form action="${request.route_path('api')}" method="post" class="add-recipient">
        <input type="text" placeholder="Full Name" name="display_name" />
        <input type="text" placeholder="Email Address" name="email" />
        <input type="hidden" name="report_id" value="${report_id}" />
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="subscription.create" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Add" />
    </form>
</%def>

<%def name="pricing_plan(plan, override_name=None, is_group=False, user=None)">
    <%
        is_active = user and user.plan_id == plan.id
    %>
    <form action="${request.route_path('api')}" method="post" class="pricing-plan ${h.text_if(is_active, 'active')}">
        <h3>${override_name or plan.name}</h3>

        <ul class="features">
            <li><span class="value">&check;</span> Feature</li>
            <li><span class="value">&check;</span> Feature</li>
        </ul>

        <p class="price">
            % if is_group:
                Starting at
            % endif
            ${plan.price_str}
        </p>

        % if user:
            <input type="hidden" name="user_id" value="${user.id}" />
        % endif

        <p class="action">
        % if is_active:
            <span>Current Plan</span>
        % else:
            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="account.plan_set" />
            <input type="hidden" name="format" value="redirect" />
            <input type="submit" value="Choose Plan" />
        % endif
        </p>
    </form>
</%def>

