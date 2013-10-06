<%inherit file="base.mako"/>

<p>
    Are you sure you want to delete your account?
    <%
        delete_url = request.route_path(
            'account_unsubscribe',
            _query={'token': c.token or '', 'confirmed': 'true'},
        )
        cancel_url = request.route_path('index')
    %>
    <a href="${delete_url}">Yes, delete everything</a> / <a href="${cancel_url}">No, take me back</a>
</p>
