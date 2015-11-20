<%inherit file="base.mako"/>

<div class="container">
    % if c.user:
    <form action="${request.route_path('account_delete')}" method="post" class="delete-confirm">
        <input type="hidden" name="token" value="${c.token or ''}" />

        <p>
            Sorry to see you go. :(
        </p>

        <p>
            <strong>How can we improve Briefmetrics for customers like yourself? All feedback is optional but very much appreciated.</strong>
        </p>

        <p>
            <label>
                Why are you leaving Briefmetrics?
                <textarea name="why" placeholder=""></textarea>
            </label>
        </p>

        <p>
            <label>
                Anything we can do to keep your business?
                <textarea name="retention" placeholder=""></textarea>
            </label>
        </p>

        <p>
            Are you sure you want to delete your account? This cannot be undone.
        </p>
        <p>
            <input type="submit" class="negative" name="confirmed" value="Yes, delete everything" style="height: 38px;" />
            <span style="padding: 0 0.5em;">or</span>
            <input type="submit" class="cta" name="feedback" value="Send feedback &amp; take me back" />
        </p>
    </form>
    % else:
    <p>
        Invalid token. Try <a href="${login_url}">signing in</a> to unsubscribe?
    </p>
    % endif
</div>
