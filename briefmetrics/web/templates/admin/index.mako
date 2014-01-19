<%inherit file="/base.mako" />


<%def name="user_status(label, is_enabled=None, link=None, on_hover=False)">
<%
    label = label.strip()
    if link:
        label = h.html.tag('a', label, attrs={'href': link})

    css = ['status']
    title = is_enabled or ''

    if is_enabled:
        css.append('enabled')
    elif not link:
        css.append('disabled')

    if on_hover:
        css.append('hidden')
%>
    <span class="${' '.join(css)}" title="${title}">${label}</span>
</%def>

<div class="container">
    <form action="${request.route_path('api')}" method="post">
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="admin.dry_run" />
        <input type="hidden" name="format" value="redirect" />

        <p>
            <input type="text" size="3" value="10" />
            <input type="submit" value="Dry Run" />
        </p>
    </form>



    <h2>Reports</h2>
    <ol>
    % for report_log in c.recent_reports:
        <li value="${report_log.report_id}">
            ${report_log.time_sent or '(Not sent)'}
            <a href="${request.route_path('admin_report_log', id=report_log.id)}">
                ${report_log.subject}
            </a>
            in ${'{:0.2}'.format(report_log.seconds_elapsed)}s
        </li>
    % endfor
    </ol>

    <h2>Users</h2>
    <ol class="user-list">
    % for u in c.users:
        <li value="${u.id}">
            <p>
                ${user_status('Token', u.account and u.account.oauth_token and u.account.oauth_token.get('refresh_token', False))}
                ${user_status(u.plan.name, u.plan_id)}
                ${user_status(('%s Remaining' % u.num_remaining) if u.num_remaining is not None else 'Paid', u.num_remaining != 0)}
                ${user_status('Card', u.stripe_customer_id)}
                ${user_status('Ghost', link=request.route_path('admin_login_as', _query={'id': u.id}), on_hover=True)}
            </p>

            <div class="id">
                "${u.account.display_name}" &lt;${u.email}&gt;

                <ol>
                % for r in u.account.reports:
                    <li value="${r.id}">${r.display_name} (next report: ${h.human_date(r.time_next)})
                % endfor
                </ol>
            </div>
        </li>
    % endfor
    </ol>

</div>
