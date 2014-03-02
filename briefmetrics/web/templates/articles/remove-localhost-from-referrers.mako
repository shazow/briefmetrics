<%inherit file="/base.mako"/>

<div class="container">
    <h2>How to remove <code>localhost</code> from my referrer list</h2>

    <p>
        If somebody on your team is running a development version of your
        application with the Google Analytics tracking code, then you'll get a
        few annoying side effects.
    </p>

    <p>
        Not only will "localhost" will show up in your Referrers, but your
        aggregate metrics like Bounce Rate, Time On Site, Conversion, and
        others will be incorrect because the unusual developer's behavior will
        be mixed in with that of normal users. We don't want that.
    </p>

    <p>
        This is easy to fix and you have a choice of three different methods, but
        it's important to note that all fixes will only apply to <em>new
        visits</em>. Existing tainted data will remain the way it is,
        unfortunately.
    </p>

    <h3>
        Add a Google Analytics exclusion filter
    </h3>

    <ol>
        <li>
            <a href="https://www.google.com/analytics/web/">Open Google Analytics</a> and choose your property view.
        </li>
        <li>
            Navigate to <code>Admin</code>.
        </li>
        <li>
            Click on <code>Filters</code> under the View column.
        </li>
        <li>
            Click on <code>New Filter</code>.
        </li>
        <li>
            Create a new "Predefined filter" which excludes traffic to the "localhost" hostname.
        </li>
    </ol>

    <p>
        Your filter should look like this:
    </p>

    <p>
        <img src="/static/images/articles/add-filter-exclude-localhost.png" />
    </p>

    <p>
        You may need to change <code>localhost</code> to whatever hostname your
        development team uses. Or better yet, if all development happens from
        the same network, you can exclude an entire IP range so that none of
        the company's behavior will affect your analytics. Just set the filter
        to exclude "traffic from ip address" and off you go.
    </p>

    <h3>
        Change the JavaScript tracking snippet to exclude a host
    </h3>

    <p>
        If you'd rather not mess with Google Analytics Filters and the
        application is fairly frontend-heavy, then making the fix in JavaScript
        is a reasonable choice.
    </p>

    <p>
        In your Google Analytics tracking snippet, find the part that queues
        the "pageview" tracking event. If you've upgraded to Universal Analytics,
        then it looks something like <code>ga('send', 'pageview')</code>.
    </p>

    <p>
        Now we want to wrap the track with a condition that checks the visitor's
        hostname for this visit. Something like this:
    </p>

    <code><pre>

    </pre></code>

    <p>
        More discussion about this on this StackOverflow thread:
        <a href="http://stackoverflow.com/questions/1251922/is-there-a-way-to-stop-google-analytics-counting-development-work-as-hits">
        Is there a way to stop Google Analytics counting development work as hits?
        </a>
    </p>
</div>
