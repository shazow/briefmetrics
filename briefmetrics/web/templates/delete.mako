<%inherit file="base.mako"/>

<div class="container">
    % if c.user:
    <form action="${request.route_path('account_delete')}" method="post" class="delete-confirm">
        <input type="hidden" name="token" value="${c.token or ''}" />
        <input type="hidden" name="confirmed" value="true" />

        <p>
            Are you sure you want to delete your account? This cannot be undone.
        </p>
        <p>
            <input type="submit" class="negative" value="Yes, delete everything" />
            <span style="padding: 0 0.5em;">or</span> <a href="${request.route_path('index')}" class="cta" style="width: 200px;">Nevermind, take me back</a>
        </p>
    </form>
    % else:
    <p>
        Invalid token. Try <a href="${request.route_path('account_login')}">signing in</a> to unsubscribe?
    </p>
    % endif
</div>
