<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<%block name="extra_head">
    <meta name="description" content="Quick overviews of your website analytics, directly to your inbox." />
    <meta name="msvalidate.01" content="094963573599E381E1E174821EBD1DCD" />
</%block>

<div class="intro">
    <h1>
        <a href="/">Briefmetrics</a> emails you simple overviews of<br \>your website's Google Analytics.
    </h1>

    <div class="inner">
        <div class="signup">
            ${widgets.login_cta(login_url)}

            <ul class="details">
                <li>No credit card required to get started.</li>
                <li><a href="/pricing">Plans</a> start at ${pricing.PLAN_PAID.price_str}.</li>
                <li>Please read our simple <a href="/privacy">Privacy Policy</a>.</li>
            </ul>
        </div>

        <section id="alert">
            <strong>Announcement</strong>: <a href="/articles/shutdown">Briefmetrics is shutting down in 2023</a>
        </section>

        <div class="preview screenshot">
            <div class="window-header">
                <ul class="window-buttons">
                    <li> </li>
                    <li> </li>
                    <li> </li>
                </ul>
                Sample Report for yoursite.com
            </div>
            <div class="email-header">
                <strong>Briefmetrics</strong> to <strong>Me</strong>
                <span class="reply-button">
                    <img src="/static/images/reply-icon.png" />
                </span>
            </div>
            <h3>Weekly Report for ${'{:%b %d, %Y}'.format(h.now())}</h3>
            <img src="/static/images/screenshot.png?1" alt="Sample Report Screenshot" />
            <p>
                ... and <a href="/features">much more</a>!
            </p>
        </div>

        <section class="features" id="features">
            <h3>Powerful Reporting, Zero Setup.</h3>

            <ul>
                <li>
                <h4><a href="/features#mobile">Web &amp; Mobile Apps</a></h4>
                    <p class="icon">
                        <img src="/static/images/device-icons.png" style="width: 50%; height: 50%;" alt="Mobile and Desktop devices" />
                    </p>
                    <p>
                        Whether you're using Google Analytics for a website or a mobile app, Briefmetrics figures out exactly what to show you automatically.
                    </p>
                </li>
                <li>
                    <h4><a href="/features#branding">Bring Your Own Logo</a></h4>
                    <p class="icon">
                        <img src="/static/images/feature-branding.png" style="width: 45%; height: 45%;" alt="Custom Logo" />
                    </p>
                    <p>
                        Be proud to share your reports with executives or clients with our <a href="/features/custom-branding-for-agencies">whitelabel Agency features</a>.
                    </p>
                </li>
                <li>
                    <h4><a href="/features#cac">KPI &amp; CAC</a></h4>
                    <p>
                        No more spreadsheets! Ecommerce and AdWords data is computed on our backend to give you valuable metrics like <a href="/features#cac">Customer Acquisition Costs and more</a>.
                    </p>
                </li>
                <li>
                    <h4><a href="/features#annotations">Intelligent Highlighting</a></h4>
                    <p>
                        We use simple lists with annotations on the most important lines, much easier to understand and skim than big two-dimensional tables.
                    </p>
                </li>
            </ul>
        </section>

    </div>
</div>

