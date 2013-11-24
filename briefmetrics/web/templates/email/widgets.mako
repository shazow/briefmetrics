<%def name="render_table(t, title, report_link, prefix_links=None)">
<% 
    if not t.rows:
        return

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

                % for tag in row.tags:
                    <strong>
                    ${tag}
                    </strong>

                    [${tag.value}]
                % endfor
            </td>
        </tr>
    % endfor
    </tbody>
</table>

</%def>

<%def name="overview_cell(table, column_id, is_percent=False, is_optional=False)">
    <%
        column = table.get(column_id)
        last_val, cur_val = table.rows[1].get(column_id), table.rows[0].get(column_id)

        if is_percent:
            formatted_val = h.human_percent(cur_val / 100.0)
        else:
            formatted_val = h.human_int(cur_val)

        delta = 0
        if last_val:
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
