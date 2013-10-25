<%def name="data_table(rows, title, report_link)">
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
        min_value = float(c.report_referrers['rows'][0][1]) * 0.005
    %>
    % for row in rows:
        % if int(row[1]) > min_value:
        <tr>
            <td class="number">${h.human_int(row[1])}</td>
            <td>${h.human_link(row[0], max_length=100)}</td>
        </tr>
        % endif
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
