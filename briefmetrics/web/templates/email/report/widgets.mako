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

    label = tag.column and tag.column.label or tag.type
    prefix = postfix = u''

    if tag.is_prefixed:
        prefix = tag.value or u''
    elif tag.value is not None:
        postfix = tag.column and tag.column.format(tag.value) or tag.value
%>

<span class="annotation ${css_class[tag.is_positive]}">${prefix}<span class="label">${label}</span>${postfix}</span>
% endfor
</%def>

<%def name="render_table(t, title=None, report_link=None, prefix_links=None, include_head=True, linkify_values=True)">
<% 
    if not t.rows:
        return ''

    columns = t.get_visible()
%>
<table>
    % if include_head:
    <thead>
        <tr>
            <td class="number">
                ${columns[0].label}
            </td>
            <td>
                ${columns[1].label}

                % if report_link:
                <a class="permalink" target="_blank" href="${report_link}">Full report</a>
                % endif
            </td>
        </tr>
    </thead>
    % endif
    <tbody>
    % for row in t.rows:
    <%
        views, url = row.get(columns[0].id), row.get(columns[1].id)

        if not linkify_values:
            link = url
        elif prefix_links and url.startswith('/'):
            link = h.human_link(prefix_links + url, url, max_length=100)
        else:
            link = h.human_link(url, max_length=100)

        inline_table = row.inline and row.inline.get(columns[1].id)
    %>
        <tr>
            <td class="number">${columns[0].format(views)}</td>
            <td>
                ${link}
                ${render_tags(row.tags)}
                <%
                    if inline_table:
                        render_table(inline_table, include_head=False)
                %>
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

        formatted_val = column.type_format(cur_val)

        delta = 0
        if last_val and cur_val:
            delta = (cur_val / float(last_val)) - 1
    %>
    <td ${h.text_if(is_optional, 'class="optional"')}>
        <strong>${formatted_val}</strong>
        <span>${column.label}</span>
        % if is_percent:
            % if delta <= 0:
                <small class="pos">${h.human_percent(delta)} decrease</small>
            % else:
                <small class="neg">${h.human_percent(delta)} increase</small>
            % endif
        % else:
            % if delta > 0:
                <small class="pos">+${h.human_percent(delta)}</small>
            % else:
                <small class="neg">${h.human_percent(delta)}</small>
            % endif
        % endif
    </td>
</%def>

<%def name="summary_cell(label, value, delta=None, is_positive=None, alt=None)">
    % if alt:
    <td title="${alt}">
    % else:
    <td>
    % endif
        <strong>${value}</strong>
        <span>${label}</span>
        % if delta:
            % if is_positive is None:
            <small>${delta}</small>
            % elif is_positive:
            <small class="pos">${delta}</small>
            % else:
            <small>${delta}</small>
            % endif
        % else:
            <small>&nbsp;</small>
        % endif
    </td>
</%def>

<%def name="render_intro(current, last, last_relative, units, interval, type='site')">
    <%
        previous_date_start, date_start, date_end = interval
        is_last_day = (date_end + h.timedelta(days=1)).month != date_end.month
        period_fmt = '%B'
        last_period = "last month"
        if (date_end - date_start).days > 360:
            period_fmt = '%Y'
            last_period = 'last year'
        if previous_date_start.year != date_start.year:
            last_period = "last {}".format(previous_date_start.strftime(period_fmt))
    %>
    Your ${type} had <span class="chartTop">${h.format_int(current, units)}
    % if is_last_day:
        in ${date_start.strftime(period_fmt)},</span>
    % else:
        so far this month</span>,
    % endif
    % if is_last_day:
        compared to <span class="chartBottom">${previous_date_start.strftime(period_fmt)}'s total of ${h.human_int(last)}</span>.
    % elif current >= last_relative and last != last_relative:
        compared to ${last_period}'s ${h.format_int(last_relative, units)} at this time.
        % if current > last:
            You're already ahead of <span class="chartBottom">${last_period}'s total of ${h.human_int(last)}</span>!
        % else:
            You're on your way to beat <span class="chartBottom">${last_period}'s total of ${h.human_int(last)}</span>.
        % endif
    % else:
        compared to <span class="chartBottom">${last_period}'s
            ${h.format_int(last_relative, units)}</span> at this time and
        ${h.human_int(last)} by the end of ${last_period}.
    % endif
</%def>
