<%inherit file="/base.mako"/>

<div class="container">
    <h2>How to remove <code>localhost</code> from my referrer list</h2>

    <p>
        If somebody on your team is running a development version of your
        application with the Google Analytics tracking code, then you'll get a
        few annoying side effects.
    </p>

    <p>
        Not only will <em>localhost</em> show up in your Referrers, but your
        aggregate metrics like Bounce Rate, Time On Site, Conversion, and
        others will be incorrect because the unusual behavior of a developer's
        will be mixed in with that of normal users and skew our results. We
        don't want that.
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

    <p>
        Adding a filter to Google Analytics might be the easiest method with
        the least intervention required from the development team.
    </p>

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
        In your Google Analytics tracking snippet, find the part which defines
        the property ID for which to record analytics. If you've upgraded to
        Universal Analytics, then it looks something like
        <code>ga('create', 'UA-XXXXXX', 'example.com');</code>.
    </p>

    <p>
        Now we want to wrap the track with a condition that checks the visitor's
        hostname for this visit. Something like this:
    </p>

    <pre class="code">
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

    <em>// Skip recording GA events to our account if in development.
    if (document.location.hostname != 'localhost') {
        ga('create', 'UA-XXXXXXX-XX', 'example.com');
    }</em>

    ga('send', 'pageview');</pre>

    <p>
        You'll need to make sure that you used your original UA-code and
        website, rather than <em>example.com</em>. If your team uses a
        development hostname other than <em>localhost</em> (such as
        <em>127.0.0.1</em>, for example), then don't forget to adjust for that.
    </p>

    <p>
        One variation of this method is to put the if-statement around the entire
        Google Analytics block, but the benefit of putting it just around the
        <code>ga('create', ...)</code> statement is that the rest of your
        Google Analytics related code will continue without actually recording
        the data to your account, rather than raise JavaScript errors.
    </p>

    <h3>
        Skip the JavaScript tracking snippet in the template
    </h3>

    <p>
        If you're using something like PHP (such as with Wordpress), you could
        do something like this in the PHP footer file which includes the Google
        Analytics snippet:
    </p>

    <pre class="code">
    &lt;? if($_SERVER["REMOTE_ADDR"] != "127.0.0.1") { ?&gt;
        &lt;script&gt; Google Analytics snippet here ...&lt;/script&gt;
    &lt;? } ?&gt;</pre>

    <p>
        Some serves are capable of setting up a global or environment variable which
        keeps track of whether the application is being run in development or
        production.
    </p>

    <p>
        If you're using Django, then your template snippet might look
        something like this...
    </p>

    <pre class="code">
    {% if not DEBUG %}
        &lt;script&gt; Google Analytics snippet here ...&lt;/script&gt;
    {% endif %}</pre>

    <p>
        Or with Ruby on Rails, it might look like this...
    </p>

    <pre class="code">
    &lt;% unless RAILS_ENV == "development" %&gt;
        &lt;script&gt; Google Analytics snippet here ...&lt;/script&gt;
    &lt;% end %&gt;</pre>

    <p>
        This method probably requires some involvement with your development
        team but it also allows to have better control over when your Google
        Analytics snippet shows up or not. This is also a great opportunity to
        add more production-specific JavaScript services into a wired-off
        development flag.
    </p>

    <h3>Moving forward...</h3>

    <p>
        With your changes in place, you'll want to double-check your Referrers
        analytics a day or two later. Make sure to select a recent date range
        that does not include days up to and including when the changes were
        made.
    </p>

    <p>
        For more discussion on this topic, check this StackOverflow thread:<br />
        <a href="http://stackoverflow.com/questions/1251922/is-there-a-way-to-stop-google-analytics-counting-development-work-as-hits">
        Is there a way to stop Google Analytics counting development work as hits?
        </a>
    </p>
</div>
