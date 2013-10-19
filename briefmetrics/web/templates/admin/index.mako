<%inherit file="/base.mako"/>

<div class="container">

    <h2>Users</h2>
    <ul>
    % for u in c.users:
        <li>
        % if u.account.oauth_token and u.account.oauth_token.get('refresh_token'):
            ✓
        % else:
            ✗
        % endif
            ${u.email} (${u.account.display_name})
            <a class="button" href="${request.route_path('admin_login_as', _query={'id': u.id})}">➠</a>
        </li>
    % endfor
    </ul>

</div>
