<%inherit file="/base.mako" />
<%namespace file="/admin/widgets.mako" name="widgets" />

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

</div>
