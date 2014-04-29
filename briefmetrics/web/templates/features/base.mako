<%inherit file="/base.mako"/>

<div class="container intro">
    ${next.body()}

    <p class="closer">
        <a class="cta" href="${login_url}">
            Sign in with Google Analytics
            <small>get your first email report now</small>
        </a>
    </p>
</div>
