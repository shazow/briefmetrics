<%def name="render_tags(tags)">
<%
    if not tags:
        return ''

    css_class = {
        None: 'neutral',
        True: 'positive',
        False: 'negative',
    }
%>
% for tag in tags:
    <%
        # TODO: Move this somewhere else
        if tag.column and tag.column.id == 'ga:avgPageLoadTime' and (not tag.value or tag.is_positive or tag.value < 2.0 or tag.value < tag.column.average * 3):
            continue
    %>

<span class="annotation ${css_class[tag.is_positive]}">
    % if tag.is_prefixed:
        ${tag.value}
    % endif
    <span class="label">
    % if tag.column:
        ${tag.column.label}
    % else:
        ${tag.type}
    % endif 
    </span>
    % if not tag.is_prefixed and tag.value:
        ${tag.column and tag.column.format(tag.value) or tag.value}
    % endif
</span>
% endfor
</%def>

<%def name="render_table(t, title, report_link, prefix_links=None)">
<% 
    if not t.rows:
        return ''

    columns = t.get_visible()
%>
<table>
    <thead>
        <tr>
            <td class="number">
                ${columns[0].label}
            </td>
            <td>
                ${columns[1].label}

                <a class="permalink" target="_blank" href="${report_link}">Full report</a>
            </td>
        </tr>
    </thead>
    <tbody>
    % for row in t.rows:
    <%
        views, url = row.get(columns[0].id), row.get(columns[1].id)

        if prefix_links and url.startswith('/'):
            link = h.human_link(prefix_links + url, url, max_length=100)
        else:
            link = h.human_link(url, max_length=100)
    %>
        <tr>
            <td class="number">${h.human_int(views)}</td>
            <td>
                ${link}

                ${render_tags(row.tags)}
            </td>
        </tr>
    % endfor
    </tbody>
</table>

</%def>

<%def name="overview_cell(table, column_id, is_percent=False, is_optional=False)">
    <%
        if len(table.rows) < 2:
            return ''

        column = table.get(column_id)
        last_val, cur_val = table.rows[1].get(column_id), table.rows[0].get(column_id)

        if is_percent:
            formatted_val = h.human_percent(cur_val)
        else:
            formatted_val = h.human_int(cur_val)

        delta = 0
        if last_val and cur_val:
            delta = (cur_val / float(last_val)) - 1
    %>
    <td ${h.text_if(is_optional, 'class="optional"')}>
        <strong>${formatted_val}</strong>
        <span>${column.label}</span>
        % if is_percent:
            % if delta <= 0:
                <small>${h.human_percent(delta)} decrease</small>
            % else:
                <small class="neg">${h.human_percent(delta)} increase</small>
            % endif
        % else:
            % if delta > 0:
                <small>+${h.human_percent(delta)}</small>
            % else:
                <small class="neg">${h.human_percent(delta)}</small>
            % endif
        % endif
    </td>
</%def>


<%def name="render_intro(current, last, last_relative, units, interval)">
    <%
        previous_date_start, date_start, date_end = interval
        is_last_day = (date_end + h.timedelta(days=1)).month != date_end.month
    %>
    Your site had <span class="chartTop">${h.format_int(current, units)}
    % if is_last_day:
        in ${date_start.strftime('%B')},</span>
    % else:
        so far this month</span>,
    % endif
    % if is_last_day:
        compared to <span class="chartBottom">${previous_date_start.strftime('%B')}'s total of ${h.human_int(last)}</span>.
    % elif current >= last_relative and last != last_relative:
        compared to last month's ${h.format_int(last_relative, units)} at this time.
        % if current > last:
            You're already ahead of <span class="chartBottom">last months's total of ${h.human_int(last)}</span>!
        % else:
            You're on your way to beat <span class="chartBottom">last months's total of ${h.human_int(last)}</span>.
        % endif
    % else:
        compared to <span class="chartBottom">last month's ${h.format_int(last_relative, units)}</span> at this time.
    % endif
</%def>
