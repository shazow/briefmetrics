<%def name="data_table(rows, title, report_link, prefix_links=None)">
<% if not rows:
    return
%>
<table>
    <thead>
        <tr>
            <td class="number">
                Views
            </td>
            <td>
                ${title}

                <a class="permalink" href="${report_link}">Full report</a>
            </td>
        </tr>
    </thead>
    <tbody>
    <%
        min_value = float(rows[0][1]) * 0.005
    %>
    % for row in rows:
    <%
        if int(row[1]) < min_value:
            continue

        url = row[0]
        if prefix_links and url.startswith('/'):
            link = h.human_link(prefix_links + url, url, max_length=100)
        else:
            link = h.human_link(url, max_length=100)

        tags = ', '.join(row[4]) if len(row) == 5 else ''
    %>
        <tr>
            <td class="number">${h.human_int(row[1])}</td>
            <td title="${tags}">
                ${link}
                ${tags}
            </td>
        </tr>
    % endfor
    </tbody>
</table>
</%def>


<%def name="overview_cell(rows, column, label, is_percent=False, is_optional=False)">
    <%
        last_val, cur_val = float(rows[1][column]), float(rows[0][column])

        if is_percent:
            formatted_val = h.human_percent(cur_val / 100.0)
        else:
            formatted_val = h.human_int(cur_val)

        delta = 0
        if last_val:
            delta = (cur_val / last_val) - 1
    %>
    <td ${h.text_if(is_optional, 'class="optional"')}>
        <strong>${formatted_val}</strong>
        <span>${label}</span>
        % if delta > 0:
            <small>+${h.human_percent(delta)}</small>
        % else:
            <small class="neg">${h.human_percent(delta)}</small>
        % endif
    </td>
</%def>
