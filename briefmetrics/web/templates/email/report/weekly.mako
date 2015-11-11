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
            ${widgets.overview_cell(r.tables['summary'], 'ga:pageviews')}
            ${widgets.overview_cell(r.tables['summary'], 'ga:bounceRate', is_percent=100.0)}
            % if r.tables['summary'].has_value('ga:itemRevenue'):
                <%
                    revenue, sales = next(r.tables['summary'].iter_formatted('ga:itemRevenue', 'ga:itemQuantity'))
                %>
                ${widgets.summary_cell('Revenue', revenue, "%s sales" % sales)}
            % endif
        </tr>
    </table>
    <%
        col_ids = 'ga:pageviews', 'ga:users', 'ga:avgSessionDuration', 'ga:bounceRate', 'ga:sessions', 'ga:goalConversionRateAll'
        rows = r.tables['summary'].iter_rows(*col_ids)
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

    % if r.tables.get('ads') and r.tables['ads'].has_value('ga:adCost'):
    <%
        t = r.tables['ads']
        col_ids = 'ga:adCost', 'ga:impressions', 'ga:adClicks', 'ga:itemRevenue', 'ga:itemQuantity'
        ad_cost, ad_impressions, ad_clicks, revenue, sales = [t.get(id).sum for id in col_ids]
        cpm = "%s CPM" % h.human_dollar((ad_cost * 100.0 * 1000.0) / (ad_impressions or 1.0))
        cpc = "%s CPC" % h.human_dollar((ad_cost * 100.0) / (ad_clicks or 1.0))

        col_ids = 'ga:adGroup', 'ga:adCost', 'ga:itemRevenue', 'ga:itemQuantity'
        group_idx, cost_idx, revenue_idx, sales_idx = [t.column_to_index[id] for id in col_ids]
        ad_revenue = revenue
        ad_sales = sales
        not_set = next((r for r in t.rows if r.values[group_idx] == '(not set)'), None)
        if not_set:
            ad_revenue -= not_set.values[revenue_idx]
            ad_sales -= not_set.values[sales_idx]

        cac = 1.0 * ad_cost / (ad_sales or 1.0)
        ad_avg_sale = ad_revenue / (ad_sales or 1.0)
    %>
    <table class="overview">
        <tr>
            ${widgets.summary_cell('Ad Spend', t.get('ga:adCost').format(ad_cost))}
            <td class="arrow">►</td>
            ${widgets.summary_cell('Impressions', t.get('ga:impressions').format(ad_impressions), cpm, alt="Advertising impressions and cost per thousand")}
            <td class="arrow">►</td>
            ${widgets.summary_cell('Ad Clicks', t.get('ga:adClicks').format(ad_clicks), cpc, alt="Advertising clicks and cost per click")}
        </tr>
    </table>

        % if ad_revenue > 0:
        <p style="margin-bottom: 2em;">
            <span class="highlight">${h.human_dollar(ad_revenue * 100.0)} revenue</span>
            is attributed to advertising campaigns across
            <span class="highlight">${h.format_int(ad_sales, u"{:,} sale")}</span>.
            Cost of acquisition is
            <span class="highlight">${h.human_dollar(cac * 100.0)} per sale</span>
            which yields
            <span class="highlight">${h.human_dollar(ad_avg_sale * 100.0)} revenue</span>
            on average.
        </p>
        % elif revenue > 0:
        <p style="margin-bottom: 2em;">
            <span class="highlight">$0 of revenue</span>
            is attributed to advertising during this period.
        </p>
        % endif
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

% if r.tables.get('keywords'):
    ${widgets.render_table(
        r.tables['keywords'],
        'Search Keywords',
        h.ga_permalink('report/trafficsources-organic', r.report, date_start=r.date_start, date_end=r.date_end),
    )}
% endif

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
