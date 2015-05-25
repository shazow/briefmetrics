<%def name="_user_status(label, is_enabled=None, link=None, on_hover=False)">
<%
    label = label.strip()
    if link:
        label = h.html.tag('a', label, attrs={'href': link})

    css = ['status']
    title = is_enabled or ''

    if is_enabled:
        css.append('enabled')
    elif not link and is_enabled is not False:
        css.append('disabled')

    if on_hover:
        css.append('hidden')
%>
    <span class="${' '.join(css)}" title="${title}">${label}</span>
</%def>

<%def name="user_render(u, header=False)">
    <div class="user">
        % if header:
            <h2>${u.display_name}</h2>
        % else:
            <h4><a href="${request.route_path('admin_user', id=u.id)}">${u.display_name}</a></h4>
        % endif
        <span class="user-status">
            ${_user_status('Token', u.account and u.account.oauth_token and u.account.oauth_token.get('refresh_token', False))}
            ${_user_status(u.plan.name, u.plan_id)}
            ${_user_status(('%s Remaining' % u.num_remaining) if u.num_remaining is not None else 'Paid', u.num_remaining != 0)}
            ${_user_status(u.payment and u.payment.id.title() or 'Card', u.payment)}
            ${_user_status(('%s Subscriptions' % len(u.subscriptions)), is_enabled=False)}

            ${_user_status('Ghost', link=request.route_path('admin_login_as', _query={'id': u.id}), on_hover=True)}
        </span>
    </div>
</%def>

