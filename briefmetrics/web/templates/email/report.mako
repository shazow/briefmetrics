<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

% if not c.report.owner.stripe_customer_id and c.report.owner.num_remaining is not None and c.report.owner.num_remaining <= 1:
    <p>
        <strong>This is your final report. :(</strong><br />
        Please <a href="https://briefmetrics.com/settings">add a credit card now</a> to keep receiving Briefmetrics reports.
    </p>

    <h3>Back to your previously scheduled report...</h3>
% endif

<p>
    Your site had <span class="chartTop">${h.human_int(c.report.data['total_current'])} views so far this month</span>,
    % if c.report.data['total_current'] >= c.report.data['total_last_relative']:
        compared to last month's ${h.human_int(c.report.data['total_last_relative'])} views at this time.
        You're on your way to beat <span class="chartBottom">last months's total of ${h.human_int(c.report.data['total_last'])}</span>.
    % else:
        compared to <span class="chartBottom">last month's ${h.human_int(c.report.data['total_last_relative'])} views</span> at this time.
    % endif
</p>

${h.chart(c.report.data['historic_data'], width=560, height=200)}

<h2>
    Last week&hellip;
    <% overlap_days = 7 - c.report.date_end.day %>
    % if overlap_days > 0:
        <span class="quiet">(includes ${h.format_int(overlap_days, '{} day')} from last month)</span>
    % endif
</h2>

% if c.report.tables.get('summary'):
    <table class="overview">
        <tr>
            ${widgets.overview_cell(c.report.tables['summary'], 'ga:visitBounceRate', is_percent=True)}
            ${widgets.overview_cell(c.report.tables['summary'], 'ga:pageviews')}
        </tr>
    </table>
    <%
        columns = 'ga:pageviews', 'ga:uniquePageviews', 'ga:avgTimeOnSite', 'ga:visitBounceRate'
        pageviews, uniques, seconds, bounces = next(c.report.tables['summary'].iter_rows(*columns))
    %>

    % if int(uniques) and float(seconds):
    <p style="margin-bottom: 2em;">
        <span class="highlight">${h.human_int(uniques)}</span>
        unique visitors each spent an average of
        <span class="highlight">${h.human_time(seconds)}</span>
        over
        <span class="highlight">${'%0.1f' % (float(pageviews) / float(uniques))}</span>
        pageviews per session.
    </p>
    % endif
% endif

${widgets.render_table(
    c.report.tables['pages'],
    'Top Pages',
    h.ga_permalink('report/content-pages', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    prefix_links='http://%s' % c.report.report.remote_data['websiteUrl'],
)}

${widgets.render_table(
    c.report.tables['referrers'],
    'Referrers',
    h.ga_permalink('report/trafficsources-referrals', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
)}

${widgets.render_table(
    c.report.tables['social_search'],
    'Social & Search',
    h.ga_permalink('report/social-sources', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
)}

<p>
    % if c.report.owner.num_remaining is None or c.report.owner.stripe_customer_id:
        You can look forward to your next report on <span class="highlight">${h.human_date(c.report.date_next)}</span>.
    % elif c.report.owner.num_remaining <= 1:
        <strong>This is your final report. :(</strong><br />
        Please <a href="https://briefmetrics.com/settings">add a credit card now</a> to keep receiving Briefmetrics reports.
    % elif c.report.owner.num_remaining > 1:
        <strong>You have <span class="highlight">${c.report.owner.num_remaining-1} free reports</span> remaining.</strong>
        <a href="https://briefmetrics.com/settings">Add a credit card now</a> to get ${c.report.owner.num_remaining-1} extra free reports!
        Your next report is scheduled for ${h.human_date(c.report.date_next)}.
    % endif
</p>

<h2>Please send feedback</h2>
<p>
    Reply to this email with comments, suggestions, requests, praise, or selfies.
</p>

<p class="footer">
    Looking for something different?
    <a href="https://briefmetrics.com/reports">Change subscription</a> &middot;
    <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">Delete account</a>
</p>
