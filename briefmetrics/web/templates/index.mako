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

    <ul style="margin: 2em 0;">
        <li><strong>Save time by having the reports come to you.</strong> Get your first report in just 15 seconds.</li>
        <li><strong>Make better decisions with dynamic reports.</strong> Each email is intelligently crafted to show only what's relevant to you.</li>
        <li><strong>Share professional reports with your colleagues.</strong> Custom branding plans available for agencies who want to benefit clients with analytics summaries.</li>
    </ul>

    <div class="signup">
        <a class="cta" href="${login_url}">
            Sign in with Google Analytics
            <small>includes 10 free email reports</small>
        </a>

        <ul class="details">
            <li>No credit card required.</li>
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
        <p>
            <a href="${login_url}">Sign up for Briefmetrics</a> to be notified of the latest articles.
        </p>
    </div>
</div>

