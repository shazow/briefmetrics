<%inherit file="base.mako"/>

<%block name="extra_head">
    <meta name="description" content="Quick overviews of your website analytics, directly to your inbox." />
</%block>

<%block name="header"></%block>

<%
    if request.features.get('ssl'):
        login_url = request.route_url('account_login', _scheme='https')
    else:
        login_url = request.route_path('account_login')
%>

<div class="container intro">

    <h1><a href="/">Briefmetrics</a></h1>

    <h2>
        Simple overviews of your website's Google Analytics, in the comfort of your Inbox.
    </h2>

    <ul class="features">
        <li>
            <strong>Set It and Forget It</strong>
            <p>
                Just 15 seconds to start receiving email reports perfect for you, no configuration required.
            </p>
        </li>
        <li>
            <strong>Actionable Analytics Emails</strong>
            <p>
                Charts and valuable data right in your inbox,
                skip the usual PDF attachments and web dashboards.
            </p>
        </li>
        <li>
            <strong>Custom Branding</strong>
            <p>
                Agency plans allow you to prepare reports for your clients with your own logo and more.
            </p>
        </li>
    </ul>

    <div class="signup">
        <a class="cta" href="${login_url}">
            Sign in with Google Analytics
            <small>includes 10 free email reports</small>
        </a>

        <ul class="details">
            <li>No credit card required to get started.</li>
            <li>${pricing.PLAN_PAID.price_monthly_str}/month after if you'd like to continue.</li>
            <li>Please read our simple <a href="/privacy">Privacy Policy</a>.</li>
        </ul>
    </div>

    <div class="screenshot preview">
        <h3>Sample Report</h3>
        <img src="/static/images/screenshot.png?1" alt="Sample Report Screenshot" height="851px"/>
        <p>
            ... and much more!
        </p>
    </div>

    <div class="closer">
        <a class="cta" href="${login_url}">
            Sign in with Google Analytics
            <small>get your first email report now</small>
        </a>
    </div>

    <div class="articles">
        <h3>Recent Articles</h3>
        <ul>
            <li>
                <a href="/articles/remove-localhost-from-referrers">How to remove localhost from your referrer list</a> and avoid skewing your valuable visitor data.
            </li>
            <li>
                <em>Coming soon:</em> Most accurate way to track outgoing clicks, and why every other tutorial gets it wrong.
            </li>
        </ul>
    </div>
</div>

