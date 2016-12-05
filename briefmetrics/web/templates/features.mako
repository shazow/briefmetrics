<%inherit file="/base.mako"/>

<div class="container feature">
    <h2>Anatomy of a Briefmetrics Report</h2>

    <section>
        <h3>Quick Preview</h3>
        <p>
            When an email lands in your inbox, most clients render the first
            line as a short preview next to the subject line. Briefmetrics
            crafts this preview to be easy to skim and informative.
        </p>
        <p>
            <img class="sample" src="/static/images/features/quick-preview.png" alt="Quick Preview" />
        </p>
        <p>
            A lot of emails get this wrong. You'll appreciate our attention to detail.
        </p>
    </section>

    <section>
        <h3>Your Branding</h3>
        <p>
            Each report is greeted with a customizeable logo. With our agency
            tiers, you can make the emails feel like they belong in your
            corporate inbox.
        </p>
        <p>
            <img class="sample" src="/static/images/features/your-branding.png" alt="Your Branding" />
        </p>
    </section>

    <section>
        <h3>Pacing Chart</h3>
        <p>
            An important metric to keep track of is how your analytics is
            performing compared to the same time during the previous month
            (Month-over-Month, or MoM pacing chart). The focal point of the report is
            the <em>pacing chart</em> which compares the progress of this month to the
            last month, allowing you to visually see the trend and set
            expectations for the coming weeks.
        </p>
        <p>
            <img class="sample" src="/static/images/features/pacing-chart.png" alt="Month over Month" />
        </p>
    </section>

    <section>
        <h3>Key Performance Indicators (KPI)</h3>
        <p>
            The rest of the report focuses on key metrics from the previous
            week (Week over Week, or WoW). We start with the basics: Views and
            bounce rate, compared to the previous week. Immediately we want to
            answer: Are the high-level metrics getting better or worse? Then we
            follow up with uniques, session time, and pages per session in an
            easy-to-consume sentence&mdash;this helps us paint the picture of
            how our visitors are behaving.
        </p>
        <p>
            <img class="sample" src="/static/images/features/kpi.png" alt="Weekly Key Performance Indicators" />
        </p>
    </section>

    <section>
        <h3>Customer Acquisition Cost (CAC)</h3>
        <p>
            With Ecommerce and Adwords linked to your Google Analytics, you'll
            see a very important section showing your total revenue for the
            week and the calculated acquisition cost.
        </p>
        <p>
            <img class="sample" src="/static/images/features/cac.png" alt="Weekly Customer Acquisition Cost" />
        </p>
        <p>
            The acquisition cost and revenue per ad conversion is spelled out
            so you can make a simple decision: <strong>Is revenue per ad-acquired
            customer exceeding your profit?</strong> If you're making money from your
            ads, then you should increase your ad spend! If you're losing money
            per ad conversion, then it's time to tweak your ads.
        </p>
    </section>

    <h2>Details &amp; Annotations</h2>
    <p>
        While Google Analytics gives you the bulk data in big tables with many rows and columns, Briefmetrics takes a different approach: We turn complicated tables into a list with values and names, then we annotate each item with tags which <strong>only highlight the extremes and important deviations</strong>.
    </p>
    <p>
        <strong>Focus on what's important:</strong> If your average bounce rate is 50% then we don't waste your time by telling you about every page which got 51% or 49% bounce rate&mdash;that's boring and not important. We only highlight pages which have the highest and lowest bounce rates, and any bounce rates which substantially deviate from the site average. You'll see pages annotated with bounce rates like 90% or 20% which are worth looking at.
    </p>
    <p>
        You'll see the most interesting rows <strong style="color:green;">highlighted with green</strong> when it's better than the site average and <strong style="color:red;">highlighted with red</strong> when it's worse than average. Put some extra time into fixing the reds, and do more of what you're doing with the greens.
    </p>

    <section>
        <h3>Top pages</h3>
        <p>
            These are the top pages on your property by the number of visits. Your landing page should be #1 here, unless you scored a great blog post recently which is driving the bulk of the traffic. You know best which pages you need to drive the most traffic to, so keep an eye on these and adjust your strategy accordingly.
        </p>
        <p>
            <img class="sample" src="/static/images/features/top-pages.png" alt="Top Page Traffic" />
        </p>
        <p>
            Mobile application reports will show <em>Screens</em> instead of Pages.
        </p>
    </section>

    <section>
        <h3>Referrers</h3>
        <p>
            Which websites are driving the most traffic to you? New referres are annotated with a <strong style="color:grey;">New</strong> tag, keep an eye on these. When a new referrer comes along, it's a good idea to thank them or even retweet their promotion to amplify the <a href="https://en.wikipedia.org/wiki/Social_proof">social proof</a> that they've given you.
        </p>
        <p>
            <img class="sample" src="/static/images/features/referrers.png" alt="Top Link Referrers" />
        </p>
    </section>

    <section>
        <h3>Social, Search, and Campaigns</h3>
        <p>
            Your organic traffic sources and advertising campaigns are showing you the fruits of your efforts in the past week. Not all traffic sources are made equal: Focus on ones with low bounce rates, high time on site, and most importantly high conversion rates. You're better off with 100 sessions from a high value demographic that buys your products than 10,000 visits who bounce immediately.
        </p>
        <p>
            <img class="sample" src="/static/images/features/organic.png" alt="Organic Traffic Sources" />
        </p>
    </section>

    <section>
        <h3>Products &amp; Sales</h3>
        <p>
            If you have Ecommerce Analytics instrumented, then you'll see a list of all your sales and revenue per product. A handy little overview to keep an eye on every week, even if you have more sophisticated sales tracking software behind the scenes.
        </p>
        <p>
            <img class="sample" src="/static/images/features/revenue.png" alt="Product Revenue" />
        </p>
    </section>

    <section>
        <h3>Mobile Versions</h3>
        <p>
            For mobile analytics, such as iOS or Android apps, you'll have a version table which lets you keep track of your users' upgrade progress. Does the latest version perform worse than the previous version? Are there more crashes? This is where you'll want to look.
        </p>
        <p>
            <img class="sample" src="/static/images/features/mobile.png" alt="Mobile Versions" />
        </p>
        <p>
            Mobile reports have a few extra relevant sections such as geographic distribution and In App Purchase (IAP) conversion data. All of this is automatically included when you pick a mobile property, Briefmetrics knows what you need.
        </p>
    </section>

    <h2>Less Is More</h2>
    <p>
        Our reporting philosophy is to provide the most utility from the least amount of data and clutter, without any complicated setup or configuration. Give it a try, you'll have your first report in under a minute:
    </p>

    <p class="closer">
        <a class="cta" href="${login_url}">
            Sign in with Google Analytics
            <small>get your first email report now</small>
        </a>
    </p>
</div>
