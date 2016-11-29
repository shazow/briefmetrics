<%inherit file="base.mako"/>

<%block name="extra_head">
    <meta name="description" content="Quick overviews of your website analytics, directly to your inbox." />
</%block>

<div class="intro">
    <h1>
        <a href="/">Briefmetrics</a> emails you simple overviews of<br \>your website's Google Analytics.
    </h1>

    <div class="inner">
        <div class="signup">
            <a class="cta" href="${login_url}">
                Sign in with Google Analytics
                <small>includes 10 free email reports</small>
            </a>

            <ul class="details">
                <li>No credit card required to get started.</li>
                <li><a href="/pricing">Plans</a> start at ${pricing.PLAN_PAID.price_str}.</li>
                <li>Please read our simple <a href="/privacy">Privacy Policy</a>.</li>
            </ul>
        </div>

        <div class="screenshot preview">
            <h3>Sample Report</h3>
            <img src="/static/images/screenshot.png?1" alt="Sample Report Screenshot" />
            <p>
                ... and much more!
            </p>
        </div>

        <div class="testimonials" id="customers">
            <h3>Happy Customers</h3>

            <p>Briefmetrics is used by many startups, design agencies, and hobbyists. Here are some nice words they'd like to share with you:</p>

            <ul class="vertical">
                <li>
                    <h4 id="customer-runscope">
                        <a href="https://runscope.com/"><img src="/static/images/customer-runscope.png" alt="Runscope" /></a>
                    </h4>
                    <blockquote>
                        &ldquo;Runscope hosts several important tools for developers, <em>Briefmetrics lets us keep track of how they're doing without spending hours navigating Google Analytics</em>. Thanks to Briefmetrics&lsquo; concise weekly reports sent to the Runscope team, everything is 200 OK.&rdquo;
                        <cite>John Sheehan, CEO at Runscope</cite>
                    </blockquote>
                </li>
                <li>
                    <h4 id="customer-namecheap">
                        <a href="https://namecheap.com/"><img src="/static/images/customer-namecheap.png" alt="Namecheap"/></a>
                    </h4>
                    <blockquote>
                        &ldquo;While Namecheap is busy supporting Internet freedom, Briefmetrics is at work sifting through our Google Analytics and crafting our weekly executive analytics report. <em>Our marketing team and executives easily consume the reports and it saves us a ton of time every week!</em>&rdquo;
                        <cite>Teddy Worcester, Head of Product at Namecheap</cite>
                    </blockquote>
                </li>
                <li>
                    <h4 id="customer-delapp">
                        <a href="http://www.delappdesign.com/"><img src="/static/images/customer-delapp.png" alt="DeLapp Design"/></a>
                    </h4>
                    <blockquote>
                        &ldquo;Our web design agency proudly includes Briefmetrics reports as a perk for being our client. With custom-branded reports, <em>our clients stay more engaged with their websites' growth which drives more iteration and business for our agency.</em>&rdquo;
                        <cite>Devon DeLapp, Principal at DeLapp Design</cite>
                    </blockquote>
                </li>
                <li>
                    <h4 id="customer-builtio">
                        <a href="https://www.built.io/"><img src="/static/images/customer-builtio.png" alt="built.io"/></a>
                    </h4>
                    <blockquote>&ldquo;Briefmetrics has enabled our team of 200+ employees to understand what our web traffic means and how our efforts correlate with our results.
                        <em>Having that kind of insight in an easily digestible format has been great for the company.</em>&rdquo;
                        <cite>Elizabeth Katzki, Marketing Manager at Built.io</cite>
                    </blockquote>
                </li>
            <ul>
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
                    <a href="/about">Who is behind Briefmetrics?</a> Hi, I'm Andrey. I used to work on Google Analytics at Google and I've built many analytics products before...
                </li>
                <li>
                    <a href="/articles/remove-localhost-from-referrers">How to remove localhost from your referrer list</a> and avoid skewing your valuable visitor data.
                </li>
                <li>
                    <em>Coming soon:</em> Most accurate way to track outgoing clicks, and why every other tutorial gets it wrong.
                </li>
            </ul>
        </div>

    </div>
</div>

