<%inherit file="/base.mako" />
<%namespace file="/admin/widgets.mako" name="widgets" />


<div class="container">
    ${widgets.user_render(c.user, header=True)}

    <div class="id">
        ${c.user.email_to}

        % if c.user.account:
            <ol>
            % for r in c.user.account.reports:
                <li value="${r.id}">${r.display_name} (next report: ${h.human_date(r.time_next)})
            % endfor
            </ol>
        % else:
            <br />(No account)
        % endif
    </div>

    % if c.user.config:
<pre>
% for k, v in c.user.config.iteritems():
${"config['{:}'] = {}".format(k, v)}
% endfor
</pre>
% endif

    % if c.recent_reports:
        <h3>Reports</h3>
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
    % endif

    % if c.invited_by:
        <h3>Invited By</h3>

        ${widgets.user_render(c.invited_by)}
    % endif

    % if c.invited:
        <h3>Invited</h3>

        <ol>
            % for u in c.invited:
            <li>
                ${widgets.user_render(u)}
            </li>
            % endfor
        </ol>
    % endif
</div>
