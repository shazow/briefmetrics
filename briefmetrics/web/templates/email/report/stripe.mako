<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<%def name="render_intro(current, last, last_relative, interval)">
    <%
        previous_date_start, date_start, date_end = interval
        is_last_day = (date_end + h.timedelta(days=1)).month != date_end.month
    %>
    You earned <span class="chartTop">${h.human_dollar(current)}
    % if is_last_day:
        in ${date_start.strftime('%B')},</span>
    % else:
        so far this month</span>,
    % endif
    % if is_last_day:
        compared to <span class="chartBottom">${previous_date_start.strftime('%B')}'s total of ${h.human_int(last)}</span>.
    % elif current >= last_relative and last != last_relative:
        compared to last month's ${h.human_dollar(last_relative)} at this time.
        % if current > last:
            You're already ahead of <span class="chartBottom">last months's total of ${h.human_int(last)}</span>!
        % else:
            You're on your way to beat <span class="chartBottom">last months's total of ${h.human_dollar(last)}</span>.
        % endif
    % else:
        compared to <span class="chartBottom">last month's ${h.human_dollar(last_relative)}</span> at this time and ${h.human_dollar(last)} by the end of last month.
    % endif
</%def>

<p>
    ${render_intro(
        current=c.report.data['total_current'],
        last=c.report.data['total_last'],
        last_relative=c.report.data['total_last_relative'],
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


% if c.report.tables['customers'].rows:
    <h3>New Customers</h3>

    ${c.report.tables['customers'].render_html()}
% else:
    <p>
        No new customers this week.
    </p>
% endif

<h3>Events</h3>
${c.report.tables['events'].render_html()}
