<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<p>
    Your site had <span class="chartTop">${h.human_int(c.total_current)} views so far this month</span>,
    % if c.total_current >= c.total_last_relative:
    compared to last month's ${h.human_int(c.total_last_relative)} views at this time.
    You're on your way to beat <span class="chartBottom">last months's total of ${h.human_int(c.total_last)}</span>.
    % else:
    compared to <span class="chartBottom">last month's ${h.human_int(c.total_last_relative)} views</span> at this time.
    % endif
</p>

${h.chart(c.historic_data, width=600, height=200)}

<h2>
    Last week
    <% overlap_days = 7 - c.date_end.day %>
    % if overlap_days > 0:
        <span class="quiet">(includes ${h.format_int(overlap_days, '{} day')} from last month)</span>
    % endif
</h2>
% if c.report_summary.get('rows'):
    <%
        pageviews, uniques, seconds = c.report_summary['rows'][0]
    %>
<p style="margin-bottom: 2em;">
    <span class="highlight">${h.human_int(uniques)}</span> unique people spent on average
    <span class="highlight">${h.human_time(float(seconds) / int(uniques))}</span> over
    <span class="highlight">${'%0.1f' % (float(pageviews) / float(uniques))}</span> pageviews
    on your site in 7 days since ${h.human_date(c.date_start)}.
</p>
% endif

${widgets.data_table(
    c.report_pages.get('rows'),
    'Pages',
    h.ga_permalink('report/content-pages', c.report, date_start=c.date_start, date_end=c.date_end),
)}

${widgets.data_table(
    c.report_referrers.get('rows'),
    'Referrers',
    h.ga_permalink('report/trafficsources-referrals', c.report, date_start=c.date_start, date_end=c.date_end),
)}

${widgets.data_table(
    c.report_social.get('rows'),
    'Referrers',
    h.ga_permalink('report/social-sources', c.report, date_start=c.date_start, date_end=c.date_end),
)}

<p>
    You can look forward to your next report on ${h.human_date(c.date_next)}.
</p>

<h2>Coming soon (aka. my shameless public TODO list)</h2>
<ul>
    <li class="done">Rewriting Briefmetrics from AppEngine + Go, to good ol' fashioned self-deployed Python. Expect something new next week!</li>
</ul>

<h2>Please send feedback!</h2>
<p>
    Reply to this email with comments, suggestions, requests, praise, or selfies.
</p>

<p class="footer">
    Looking for something different?
    <a href="http://briefmetrics.com/settings">Change subscription</a> &middot;
    <a href="http://briefmetrics.com/account/disconnect?token=${c.user.unsubscribe_token}">Delete account</a>
</p>
