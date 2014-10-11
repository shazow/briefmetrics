<%def name="payment_form_body(submit_text='Start plan')">
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
            <input type="submit" class="submit-button" value="${submit_text}" />
        </label>
    </div>
</%def>


<%def name="payment_form(plan=None)">
    <form action="${request.route_path('api')}" method="post" class="payment" autocomplete="on">
        % if plan:
            <div>
                <label>
                    Plan
                    <div>
                        <input type="hidden" name="plan_id" value="${plan.id}" />
                        <strong>
                            ${plan.name}
                        </strong>
                        at ${plan.price_str}

                        <a href="/pricing" class="button">Change Plan</a>
                    </div>
                </label>
            </div>

            ${payment_form_body("Start Plan")}
        % else:
            ${payment_form_body("Update Card")}
        % endif

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.payments_set" />
        <input type="hidden" name="format" value="redirect" />
    </form>
</%def>

<%def name="payment_cancel()">
    <form action="${request.route_path('api')}" method="post" class="payment-cancel" onsubmit="return confirm('Are you sure you want to cancel your subscription? Reports will be suspended until you add another credit card.');">
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.payments_cancel" />
        <input type="hidden" name="format" value="redirect" />

        <p>
            <input type="submit" class="negative" value="Cancel Subscription" />
            <span class="button-note">Forget your credit card information and suspend your plan.</span>
        </p>
    </form>
</%def>

<%def name="report_new(available_profiles, report_types, account_id='')">
    % if not available_profiles:
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
            % for item in available_profiles:
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
            <input type="hidden" name="account_id" value="${account_id}" />
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

<%def name="site_config(site, is_active=True, is_admin=False, accounts_by_service=None)">
    <%
        anchor = 'report-{}'.format(site.report.id)
        accounts_by_service = accounts_by_service or {}
    %>
    <div class="preview report" id="${anchor}">
        <nav>
            <h3>
                ${site.display_name}
            </h3>

            <div class="controls">
                % if site.report.account.service == 'stripe':
                    <a class="button external" target="_blank" href="https://dashboard.stripe.com/">Stripe</a>
                % else:
                    % for stripe_account in accounts_by_service.get('stripe', []):
                        % if site.report.remote_data.get('webPropertyId') not in (stripe_account.config.get('ga_funnels') or []):
                            <a class="button" href="${request.route_path('api', _query=dict(
                                from_account_id=stripe_account.id,
                                to_report_id=site.report.id,
                                method="funnel.create",
                                format='redirect',
                                csrf_token=session.get_csrf_token())
                            )}">Attach Stripe <em>${stripe_account.display_name}</em> Ecommerce</a>
                        % endif
                    % endfor
                    <a class="button external" target="_blank" href="${h.ga_permalink('report/visitors-overview', site.report)}">Google Analytics</a>
                % endif
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

<%def name="combine_reports(reports, filter_types='week')">
    <%
        reports = [r for r in reports if r.type == filter_types]
        if len(reports) < 2:
            return ''
    %>
    <form action="${request.route_path('api')}" method="post" class="combine-reports">
        <p>
        % for r in reports:
            <label><input type="checkbox" name="report_ids" value="${r.id}" checked="checked" /> ${r.display_name}</label>
        % endfor
        </p>
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="report.combine" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Combine Reports" />
    </form>
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

<%def name="pricing_plan(plan, user=None)">
    <%
        is_active = user and user.plan_id == plan.id
        value_map = {
        True: u'✓',
        None: u'Unlimited',
        }
    %>
    <form action="${request.route_path('settings')}" method="post" class="pricing-plan ${h.text_if(is_active, 'active')}">
        <h3>${plan.name}</h3>

        <ul class="features">
        % for feature, value in plan.iter_features():
            <li>
                <span class="value">${value_map.get(value) or value}</span>
                ${feature.name}
            </li>
        % endfor
        </ul>

        <p class="price">
            % if plan.is_group:
                Starting at
            % endif
            <span class="value">${plan.price_monthly_str}/month</span>
        </p>

        % if user:
            <input type="hidden" name="user_id" value="${user.id}" />
        % endif

        <p class="action">
        % if is_active:
            <span>Current Plan</span>
        % else:
            <input type="hidden" name="plan_id" value="${plan.id}" />
            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="settings.plan" />
            <input type="hidden" name="format" value="redirect" />
            <input type="hidden" name="next" value="${request.route_path('settings')}" />
            <input type="submit" value="Choose Plan" />
        % endif
        </p>
    </form>
</%def>

<%def name="pricing_plan_group(plan_group, selected_plan_id=None)">
    <div class="pricing-plan-group">
        <p>
            We have some variations of the ${c.selected_plan.in_group.name} plan.
        </p>
        <ul class="vertical">
            <%
                is_upgrade = False
            %>
            % for plan in c.selected_plan.in_group.plans:
                <%
                    if plan.id == selected_plan_id:
                        is_upgrade = True
                        continue
                %>
                <li>
                    % if is_upgrade:
                    <a href="${request.current_route_path(
                        _query=dict(plan_id=plan.id, method="settings.plan", csrf_token=session.get_csrf_token())
                        )}" class="button">Upgrade</a>
                    % else:
                    <a href="${request.current_route_path(
                        _query=dict(plan_id=plan.id, method="settings.plan", csrf_token=session.get_csrf_token())
                        )}" class="button negative">Downgrade</a>
                    % endif
                    <strong>${plan.name}</strong> at ${plan.price_str}
                </li>
            % endfor
        </ul>
    </div>
</%def>

<%def name="custom_branding(user, enable_logo=True)">
    <form action="${request.route_path('settings')}" method="post" enctype="multipart/form-data" class="custom-branding">

        % if enable_logo:
        <label class="upload-drop">
            Header Logo

            <p class="note">
                Centered image maximum 580px wide. Will be converted to a PNG.
            </p>

            <blockquote>
                <img src="/static/images/email_headers/${user.config.get('email_header_image') or u'briefmetrics.png'}" />
            </blockquote>

            <div>
                <input type="file" name="header_logo" />
            </div>
        </label>
        % endif

        <label>
            Header Text

            <p class="note">
                A good place to add an introduction or phone number for
                support, but the text will push the charts further below the
                fold which may affect your recipient's engagement with the
                stats.
            </p>
            <div>
                <textarea name="header_text" placeholder="(Optional)">${user.config.get('email_intro_text') or ''}</textarea>
            </div>
        </label>


        <label>
            From Name

            <p class="note">
                The name of the report email sender. This can be your company's name.
            </p>

            <div>
                <input type="text" name="from_name" placeholder="Briefmetrics" value="${c.user.config.get('from_name') or ''}" />
            </div>
        </label>

        <label>
            Reply-to Email

            <p class="note">
                All reports are sent from support@briefmetrics.com but you can
                change the reply-to address so that your recipients will reach
                out to you with questions or feedback.
            </p>
            <div>
                <input type="email" name="reply_to" placeholder="support@briefmetrics.com" value="${c.user.config.get('reply_to') or ''}" />
            </div>
        </label>


        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.branding" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Save Changes" />
    </form>
</%def>

<%def name="account_connections(user, extra_services='')">
    % if extra_services:
    <p>
        Connect additional services to enable more features.
    </p>
    % endif
    <ul>
    % for account in sorted(user.accounts, key=lambda a: a.service):
        <li>
            <a class="button negative" href="${request.route_path('account_disconnect', _query={'account_id': account.id})}">Disconnect</a>
            <strong>${account.service_api.label}</strong>
        </li>
    % endfor
    % for service_api in extra_services:
        <li>
            <a class="button" href="${request.route_path('account_login', service=service_api.id)}">Connect</a>
            <strong>${service_api.label}</strong>
            <small>${service_api.description}</small>
        </li>
    % endfor
    </ul>
</%def>
