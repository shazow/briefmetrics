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


<%def name="payment_form()">
    <form action="${request.route_path('api')}" method="post" class="payment" autocomplete="on">
        <div>
            <label>
                Plan
                <div>
                    <%
                        plans = [p for p in pricing.PLANS if not p.is_hidden]
                    %>
                    % if len(plans) == 1:
                        <input type="hidden" name="plan_id" value="${plans[0].id}" />
                        <strong>
                            ${plans[0].option_str}
                        </strong>
                    % else:
                        <select name="plan_id">
                        % for plan in plans:
                            <option value="${plan.id}">
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
        <input type="hidden" name="method" value="settings.payments" />
        <input type="hidden" name="format" value="redirect" />
    </form>
</%def>

<%def name="report_new(available_profiles)">
    % if not available_profiles:
        <p>
            <strong>Briefmetrics was unable to load a list of your Google Analytics properties.</strong> Are you sure you signed in with the correct Google account? 
        </p>
        <p>
            You can delete this account below and try signing in again with a different account.
        </p>
        <p>
            If you don't have any Google Analytics accounts, then Briefmetrics won't be useful for you yet. :)
        </p>
        <% return '' %>
    % endif

    <form action="${request.current_route_path()}" method="post" id="create-report">
        <p class="row">
            <select name="remote_id" data-placeholder="Choose a site" style="width: 80%">
                <option />
            % for item in available_profiles['items']:
                <%
                    subscribe_url = request.route_path(
                        'settings',
                        _query={'profile_id': item['id'], 'method': 'settings.subscribe'},
                    )
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

            <select name="type" style="width: 19%; margin-right: 0; margin-left: 0.5em;">
                <option value="day">Daily</option>
                <option value="week" selected>Weekly</option>
                <option value="month">Monthly</option>
            </select>
        </p>

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="report.create" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Create Report" />
    </form>
</%def>

<%def name="report_config(report, is_active=True, is_admin=False)">
    <form action="${request.current_route_path()}" method="post" class="preview report">
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="report.update" />
        <input type="hidden" name="format" value="redirect" />
        <input type="hidden" name="report_id" value="${report.id}" />

        <nav>
            <h3>
                ${report.display_name}
            </h3>
            <div class="controls">
                <a class="button" target="_blank" href="${h.ga_permalink('report/visitors-overview', report)}">Google Analytics</a>
                % if is_admin:
                    <a class="button" target="_blank" href="${request.route_path('reports_view', id=report.id)}">Last email</a>
                % endif
                <input type="submit" name="delete" value="Delete" class="negative" />
            </div>
        </nav>

        <div class="details">
            <dl>
                <dt>Frequency</dt>
                <dd>${report.type.title()}ly</dd>
            </dl>
            <dl>
                <dt>Next Email</dt>
            % if is_active:
                <dd>
                    No reports remaining.<br />
                    <a href="/settings#credit-card">Upgrade to resume.</a>
                </dd>
            % else:
                <dd>
                    ${h.human_date(report.time_next) or 'Imminently'}
                </dd>
            % endif
            </dl>
            % if is_admin:
            <dl>
                <dt>Preferred Time</dt>
                <dd>
                    ${"{d:%A}s at {d:%H:%M} UTC".format(d=report.time_preferred or report.encode_preferred_time())}
                </dd>
            </dl>
            % endif
        </div>
    </form>
</%def>
