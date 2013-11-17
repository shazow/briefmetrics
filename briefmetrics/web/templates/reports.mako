<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

<section id="plan">
    ${widgets.plan_summary(has_card=c.user.stripe_customer_id, num_remaining=c.user.num_remaining)}
</section>

<section id="new-report">
    <h2>New report</h2>

    % if c.available_profiles:
    <form action="${request.current_route_path()}" method="post">
        <p>
            <select name="remote_id" data-placeholder="Choose a site" id="available-profiles">
                <option />
            % for item in c.available_profiles['items']:
                <%
                    subscribe_url = request.route_path(
                        'settings',
                        _query={'profile_id': item['id'], 'method': 'settings.subscribe'},
                    )
                    human_url = h.human_url(item.get('websiteUrl')) or item['name']
                    name = h.human_url(item['name'])
                %>
                <option value="${item['id']}">
                    ${human_url}
                    % if name not in ['All Web Site Data', human_url]:
                    ${name}
                    % endif
                    [${item['webPropertyId']}]
                </option>
            % endfor
            </select>
        </p>

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="report.create" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Create Report" />
    </form>
    % else:
    <p>
        <strong>Briefmetrics was unable to load a list of your Google Analytics properties.</strong> Are you sure you signed in with the correct Google account? 
    </p>
    <p>
        You can delete this account below and try signing in again with a different account.
    </p>
    <p>
        If you don't have any Google Analytics accounts, then Briefmetrics won't be useful for you yet. :)
    </p>
    % endif
</section>

% if c.reports:
<section id="active-reports">
    <h2>Active reports</h2>

    % for report in sorted(c.reports, key=lambda r: r.display_name):
        <form action="${request.current_route_path()}" method="post" class="preview report">
            <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
            <input type="hidden" name="method" value="report.update" />
            <input type="hidden" name="format" value="redirect" />
            <input type="hidden" name="report_id" value="${report.id}" />

            <nav>
                <h3>
                    ${report.display_name}
                </h3>
                <div class="controls">
                    <a class="button" target="_blank" href="${h.ga_permalink('report/visitors-overview', report)}">Google Analytics</a>
                    % if c.user.is_admin:
                        <a class="button" target="_blank" href="${request.route_path('reports_view', id=report.id)}">Last email</a>
                    % endif
                    <input type="submit" name="delete" value="Delete" class="negative" />
                </div>
            </nav>

            <div class="details">
                <dl>
                    <dt>Frequency</dt>
                    <dd>${report.type.title()}ly</dd>
                </dl>
                <dl>
                    <dt>Next Email</dt>
                % if c.user.num_remaining == 0 and not c.user.stripe_customer_id:
                    <dd>No reports remaining. Upgrade to resume.</dd>
                % else:
                    <dd>
                        ${h.human_date(report.time_next) or 'Imminently'}
                    </dd>
                % endif
                </dl>
                % if c.user.is_admin:
                <dl>
                    <dt>Preferred Time</dt>
                    <dd>
                        ${"{d:%A}s at {d:%H:%M} UTC".format(d=report.time_preferred or report.encode_preferred_time())}
                    </dd>
                </dl>
                % endif
            </div>
        </form>
    % endfor
</section>
% endif

</div>

<%block name="tail">
${h.javascript_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.jquery.min.js')}
<script type="text/javascript">
    $(function() {
         $("#available-profiles").chosen();
    });
</script>
</%block>

<%block name="extra_head">
${h.stylesheet_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.min.css')}
</%block>
