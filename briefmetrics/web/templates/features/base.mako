<%inherit file="/base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<div class="container feature">
    ${next.body()}

    <p class="closer">
        ${widgets.login_cta(login_url)}
    </p>
</div>
