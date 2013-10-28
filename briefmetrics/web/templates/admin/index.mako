<%inherit file="/base.mako" />

<%def name="user_status(label, is_enabled=None, link=None)">
<%
    label = label.strip()
    if link:
        label = h.html.tag('a', label, attrs={'href': link})
%>
    % if is_enabled:
        <span class="status enabled" title="${is_enabled or ''}">${label}</span>
    % elif not is_enabled and not link:
        <span class="status disabled">${label}</span>
    % else:
        <span class="status" title="${is_enabled}">${label}</span>
    % endif
</%def>

<div class="container">

    <h2>Users</h2>
    <ol>
    % for u in c.users:
        <li value="${u.id}">
            <p>
                ${user_status('Token', u.account.oauth_token and u.account.oauth_token.get('refresh_token', False))}
                ${user_status(u.plan.title() if u.plan else 'Plan', u.plan)}
                ${user_status(('%s Remaining' % u.num_remaining) if u.num_remaining is not None else 'Paid', u.num_remaining != 0)}
                ${user_status('Card', u.stripe_customer_id)}
                ${user_status('Ghost', link=request.route_path('admin_login_as', _query={'id': u.id}))}
            </p>

            "${u.account.display_name}" &lt;${u.email}&gt;

            <ul>
            % for r in u.account.reports:
                <li>${r.display_name} (next report: ${h.human_date(r.time_next)})
            % endfor
            </ul>
        </li>
    % endfor
    </ol>

</div>
