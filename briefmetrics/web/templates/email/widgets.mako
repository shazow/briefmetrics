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
