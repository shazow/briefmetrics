<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<%def name="render_weekly(r)">
<p>
    ${widgets.render_intro(
        current=r.data['total_current'],
        last=r.data['total_last'],
        last_relative=r.data['total_last_relative'],
        units=r.data['total_units'],
        interval=(r.data.get('total_last_date_start', r.previous_date_start), r.date_start, r.date_end),
    )}
</p>

${h.chart(r.data['historic_data'], width=560, height=200)}

<%
    interval_label = r.data.get('interval_label')
%>

<h2>
    % if interval_label:
        Last ${interval_label}&hellip;
    % else:
        Last week&hellip;
        <% overlap_days = 7 - r.date_end.day %>
        % if overlap_days > 0:
            <span class="quiet">(includes ${h.format_int(overlap_days, '{} day')} from last month)</span>
        % endif
    % endif
</h2>

% if r.tables.get('summary'):
    <table class="overview">
        <tr>
            ${widgets.overview_cell(r.tables['summary'], 'ga:visitBounceRate', is_percent=100.0)}
            ${widgets.overview_cell(r.tables['summary'], 'ga:pageviews')}
        </tr>
    </table>
    <%
        columns = 'ga:pageviews', 'ga:visitors', 'ga:avgTimeOnSite', 'ga:visitBounceRate', 'ga:visits', 'ga:goalConversionRateAll'
        rows = r.tables['summary'].iter_rows(*columns)
        pageviews, uniques, seconds, bounces, visits, conversion = next(rows)
    %>

    % if uniques and seconds:
    <p style="margin-bottom: 2em;">
        <span class="highlight">${h.human_int(uniques)} unique visitors</span>
        each spent an average of
        <span class="highlight">${h.human_time(seconds)}</span>
        over
        <span class="highlight">${'%0.1f' % (float(pageviews or 0.0) / float(visits or 1.0))} pages</span>
        % if not conversion or conversion < 0.1:
            per session.
        % else:
            per session, with a combined conversion rate of
            <span class="highlight">${h.human_percent(conversion, denominator=100.0)}</span>.
        % endif
    </p>
    % endif
% endif

${widgets.render_table(
    r.tables['pages'],
    'Top Pages',
    h.ga_permalink('report/content-pages', r.report, date_start=r.date_start, date_end=r.date_end),
    prefix_links=r.base_url,
)}

${widgets.render_table(
    r.tables['referrers'],
    'Referrers',
    h.ga_permalink('report/trafficsources-referrals', r.report, date_start=r.date_start, date_end=r.date_end),
)}

${widgets.render_table(
    r.tables['social_search'],
    'Social & Search',
    h.ga_permalink('report/social-sources', r.report, date_start=r.date_start, date_end=r.date_end),
)}

% if r.tables.get('goals'):
    ${widgets.render_table(
        r.tables['goals'],
        'Goals',
        h.ga_permalink('report/conversions-goals-overview', r.report, date_start=r.date_start, date_end=r.date_end),
    )}
% endif

% if r.tables.get('ecommerce'):
    ${widgets.render_table(
        r.tables['ecommerce'],
        'Ecommerce',
        h.ga_permalink('report/conversions-ecommerce-overview', r.report, date_start=r.date_start, date_end=r.date_end),
    )}
% endif
</%def>


${render_weekly(r=c.report)}
