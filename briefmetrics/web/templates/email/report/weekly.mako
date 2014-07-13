<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<p>
    ${widgets.render_intro(
        current=c.report.data['total_current'],
        last=c.report.data['total_last'],
        last_relative=c.report.data['total_last_relative'],
        units=c.report.data['total_units'],
        interval=(c.report.data.get('total_last_date_start', c.report.previous_date_start), c.report.date_start, c.report.date_end),
    )}
</p>

${h.chart(c.report.data['historic_data'], width=560, height=200)}

<%
    interval_label = c.report.data.get('interval_label')
%>

<h2>
    % if interval_label:
        Last ${interval_label}&hellip;
    % else:
        Last week&hellip;
        <% overlap_days = 7 - c.report.date_end.day %>
        % if overlap_days > 0:
            <span class="quiet">(includes ${h.format_int(overlap_days, '{} day')} from last month)</span>
        % endif
    % endif
</h2>

% if c.report.tables.get('summary'):
    <table class="overview">
        <tr>
            ${widgets.overview_cell(c.report.tables['summary'], 'ga:visitBounceRate', is_percent=100.0)}
            ${widgets.overview_cell(c.report.tables['summary'], 'ga:pageviews')}
        </tr>
    </table>
    <%
        columns = 'ga:pageviews', 'ga:visitors', 'ga:avgTimeOnSite', 'ga:visitBounceRate', 'ga:visits', 'ga:goalConversionRateAll'
        rows = c.report.tables['summary'].iter_rows(*columns)
        pageviews, uniques, seconds, bounces, visits, conversion = next(rows)
    %>

    % if uniques and seconds:
    <p style="margin-bottom: 2em;">
        <span class="highlight">${h.human_int(uniques)} unique visitors</span>
        each spent an average of
        <span class="highlight">${h.human_time(seconds)}</span>
        over
        <span class="highlight">${'%0.1f' % (float(pageviews or 0.0) / float(visits or 1.0))} pages</span>
        % if not conversion:
            per session.
        % else:
            per session, with a total conversion rate of
            <span class="highlight">${h.human_percent(conversion, denominator=100.0)}</span>.
        % endif
    </p>
    % endif
% endif

${widgets.render_table(
    c.report.tables['pages'],
    'Top Pages',
    h.ga_permalink('report/content-pages', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    prefix_links=c.report.base_url,
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

% if c.report.tables.get('goals'):
    ${widgets.render_table(
        c.report.tables['goals'],
        'Goals',
        h.ga_permalink('report/conversions-goals-overview', c.report.report, date_start=c.report.date_start, date_end=c.report.date_end),
    )}
% endif
