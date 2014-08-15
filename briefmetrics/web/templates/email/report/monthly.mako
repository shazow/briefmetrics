<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<%
    total_units, total_current, current_month, current_month_days, total_last, last_month, last_month_days = h.get_many(c.report.data, [
        'total_units', 'total_current', 'current_month', 'current_month_days', 'total_last', 'last_month', 'last_month_days'])
%>

<p>
    Your site had <span class="chartTop">${h.format_int(total_current, total_units)}</span>
    in ${current_month} (average of ${h.format_int(float(total_current)/current_month_days)} per day),<br />
    compared to ${last_month}'s <span class="chartBottom">${h.format_int(total_last, total_units)}</span>
    (average of ${h.format_int(float(total_last)/last_month_days)} per day).
</p>

${h.chart(c.report.data['historic_data'], width=560, height=200)}

<h2>Last month&hellip;</h2>

% if c.report.tables.get('summary'):
    <%
        columns = 'ga:pageviews', 'ga:visitors', 'ga:avgTimeOnSite', 'ga:visitBounceRate', 'ga:visits'
        pageviews, uniques, seconds, bounces, visits = next(c.report.tables['summary'].iter_rows(*columns))
    %>

    % if uniques and seconds:
    <p style="margin-bottom: 2em;">
        <span class="highlight">${h.human_int(uniques)} unique visitors</span>
        each spent an average of
        <span class="highlight">${h.human_time(seconds)}</span>
        over
        <span class="highlight">${'%0.1f' % (float(pageviews or 0.0) / float(visits or 1.0))} pages</span>
        per session.
        <span class="highlight">${h.human_percent(bounces, denominator=100.0)} of visits</span> bounced after a single page view.
    </p>
    % endif
% endif

${widgets.render_table(
    c.report.tables['geo'],
    'Countries',
    h.ga_permalink('report/visitors-geo', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    prefix_links=c.report.base_url,
)}

${widgets.render_table(
    c.report.tables['device'],
    'Devices',
    h.ga_permalink('report/visitors-mobile-overview', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    prefix_links=c.report.base_url,
)}

${widgets.render_table(
    c.report.tables['browser'],
    'Browsers',
    h.ga_permalink('report/visitors-browser', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    prefix_links=c.report.base_url,
)}

