<%inherit file="base_email.mako"/>

${h.chart(c.historic_data, width=600, height=200)}

<h2>Last week</h2>
% if c.report_summary.get('rows'):
    <%
        pageviews, uniques, seconds = c.report_summary['rows'][0]
    %>
<p style="margin-bottom: 2em;">
    <span class="highlight">${h.human_int(uniques)}</span> unique people each spent
    <span class="highlight">${h.human_time(float(seconds) / int(uniques))}</span> over
    <span class="highlight">${'%0.1f' % (float(pageviews) / float(uniques))}</span> pageviews
    on your site in 7 days since ${h.human_date(c.date_start)}.
</p>
% endif

% if c.report_pages.get('rows'):
    <table>
        <thead>
            <tr>
                <td>
                    Views
                </td>
                <td>
                    <a href="${h.ga_permalink('report/content-pages', c.report, date_start=c.date_start, date_end=c.date_end)}">Pages</a>
                </td>
            </tr>
        </thead>
        <tbody>
            % for row in c.report_pages['rows']:
            <tr>
                <td class="number">${h.human_int(row[1])}</td>
                <td><a href="${c.base_url}${row[0]}">${row[0]}</a></td>
            </tr>
            % endfor
        </tbody>
    </table>
% else:
    <h3>
        <a href="${h.ga_permalink('report/content-pages', c.report, date_start=c.date_start, date_end=c.date_end)}">No Page Visits</a>
    </h3>
% endif

% if c.report_referrers.get('rows'):
    <table>
        <thead>
            <tr>
                <td>
                    Views
                </td>
                <td>
                    <a href="${h.ga_permalink('report/trafficsources-referrals', c.report, date_start=c.date_start, date_end=c.date_end)}">Referrers</a>
                </td>
            </tr>
        </thead>
        <tbody>
            % for row in c.report_referrers['rows']:
            <tr>
                <td class="number">${h.human_int(row[1])}</td>
                <td>${h.human_link(row[0])}</td>
            </tr>
            % endfor
        </tbody>
    </table>
% else:
    <h3>
        <a href="${h.ga_permalink('report/trafficsources-referrals', c.report, date_start=c.date_start, date_end=c.date_end)}">No Referrers</a>
    </h3>
% endif

% if c.report_social.get('rows'):
    <table>
        <thead>
            <tr>
                <td>
                    Views
                </td>
                <td>
                    <a href="${h.ga_permalink('report/social-sources', c.report, date_start=c.date_start, date_end=c.date_end)}">Social</a>
                </td>
            </tr>
        </thead>
        <tbody>
            % for row in c.report_social['rows']:
            <tr>
                <td class="number">${h.human_int(row[1])}</td>
                <td>${row[0]}</td>
            </tr>
            % endfor
        </tbody>
    </table>
% else:
    <h3>
        <a href="${h.ga_permalink('report/social-sources', c.report, date_start=c.date_start, date_end=c.date_end)}">No Social Sources</a>
    </h3>
% endif

    <p>
        You can look forward to your next report on ${h.human_date(c.date_next)}.
    </p>

    <h2>Coming soon (aka. my shameless public TODO list)</h2>
    <ul>
        <li class="done">Rewriting Briefmetrics from AppEngine + Go, to good ol' fashioned self-deployed Python. Expect something new next week!</li>
    </ul>

    <h2>Please send feedback!</h2>
    <p>
        Reply to this email with comments, suggestions, requests, praise, or selfies.
    </p>

    <p class="footer">
        Looking for something different?
        <a href="http://www.briefmetrics.com/settings">Change subscription</a> &middot;
        <a href="http://www.briefmetrics.com/account/disconnect?token=${c.user.unsubscribe_token}">Delete account</a>
    </p>
