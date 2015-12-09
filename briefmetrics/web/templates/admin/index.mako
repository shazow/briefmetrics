<%inherit file="/base.mako" />
<%namespace file="/admin/widgets.mako" name="widgets" />

<div class="container">
    <form action="${request.route_path('api')}" method="post">
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="admin.dry_run" />
        <input type="hidden" name="format" value="redirect" />

        <p>
            <input type="text" size="4" value="" name="num_extra"  placeholder="extra" />
            <input type="text" size="4" value="" name="filter_account" placeholder="filter" />
            <input type="submit" value="Dry Run" />
        </p>
    </form>


    <section>
        <h2>Recent Reports</h2>
        <ol>
        % for report_log in c.recent_reports:
            <li value="${report_log.report_id}">
                ${report_log.time_sent or '(Not sent)'}
                <a href="${request.route_path('admin_report_log', id=report_log.id)}">
                    ${report_log.subject}
                </a>
                in ${'{:0.2f}'.format(report_log.seconds_elapsed)}s
            </li>
        % endfor
        </ol>
    </section>

    <section>
        <h2>Plans</h2>

        <p><strong>${c.num_active_customers}</strong>
            active customers
            expected to pay
            <strong>${h.human_dollar(c.num_mrr)}/mo</strong>.</p>

        <ul class="vertical">
        % for count, plan_id in sorted(c.by_plan, reverse=True):
            <li><strong style="display: inline-block; min-width: 8em;">${count}</strong> ${plan_id}</li>
        % endfor
        </ul>

        <h2>Payment providers</h3>

        <ul class="vertical">
        % for count, payment_id in sorted(c.by_payment, reverse=True):
            <li><strong style="display: inline-block; min-width: 8em;">${count}</strong> ${payment_id}</li>
        % endfor
        </ul>
    </section>

    <section>
    <h2>Expiring Soon (${len(c.expiring_trials)} / ${len(c.active_trials)})</h2>

        <ol class="user-list" id="expiring-trials">
        % for u in c.expiring_trials:
            <li value="${u.id}">
                ${widgets.user_render(u)}

                <div class="id">
                    <div>${u.email_to}</div>
                    <small>Joined ${h.human_date(u.time_created, max_unit='year')}</small>

                    % if u.account:
                        <ol>
                        % for r in u.account.reports:
                            <li value="${r.id}">${r.display_name} (next report: ${h.human_date(r.time_next)})
                        % endfor
                        </ol>
                    % else:
                        <br />(No account)
                    % endif
                </div>
            </li>
        % endfor
        </ol>
    </section>


    <section>
        <h2>Active Users (${len(c.active_users)} / ${c.num_users})</h2>

        <ol class="user-list" id="active-users">
        % for u in c.active_users:
            <li value="${u.id}">
                ${widgets.user_render(u)}

                <div class="id">
                    <div>${u.email_to}</div>
                    <small>Joined ${h.human_date(u.time_created, max_unit='year')}</small>

                    % if u.account:
                        <ol>
                        % for r in u.account.reports:
                            <li value="${r.id}">${r.display_name} (next report: ${h.human_date(r.time_next)})
                        % endfor
                        </ol>
                    % else:
                        <br />(No account)
                    % endif
                </div>
            </li>
        % endfor
        </ol>
    </section>

    <section>
        <h2 onclick="$('#inactive-users').toggle()">Inactive Users (${len(c.inactive_users)})</h2>

        <ol class="user-list" id="inactive-users" style="display: none;">
        % for u in c.inactive_users:
            <li value="${u.id}">
                ${widgets.user_render(u)}

                <div class="id">
                    ${u.email_to}

                    % if u.account:
                        <ol>
                        % for r in u.account.reports:
                            <li value="${r.id}">${r.display_name} (next report: ${h.human_date(r.time_next)})
                        % endfor
                        </ol>
                    % else:
                        <br />(No account)
                    % endif
                </div>
            </li>
        % endfor
        </ol>
    </section>


</div>
