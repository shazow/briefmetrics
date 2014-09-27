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
        ${forms.report_new(c.available_profiles, report_types=c.report_types, account_id=c.google_account.id)}
    % else:
        <a href="${login_url}?force=1">Connect your Google Analytics account</a>
    % endif
</section>

<%
    event_connected_accounts = [a for a in c.accounts_by_service.get('stripe') if a.config.get('ga_funnels')]
%>
% if event_connected_accounts:
<section id="event-connections">
    <h2>Event connections</h2>
% for account in event_connected_accounts:
    <h3><em>${account.display_name}</em> on Stripe</h3>

    <p>
        Converting transactions into Google Analytics Ecommerce events on these tracking codes:<br />
        ${', '.join(account.config.get('ga_funnels'))}
        <a class="button negative" href="${request.route_path('api', _query={
            'method': 'funnel.clear',
            'account_id': account.id,
            'format': 'redirect',
            'csrf_token': session.get_csrf_token(),
        })}">Clear</a>
    </p>
% endfor
</section>
% endif

% if c.reports:
<section id="active-reports">
    <h2>Active reports</h2>

    % for site in c.sites:
        ${forms.site_config(
            site,
            is_active=c.user.num_remaining != 0 or c.user.stripe_customer_id,
            is_admin=c.user.is_admin,
            accounts_by_service=c.accounts_by_service,
        )}
    % endfor
</section>
% endif

</div>

<%block name="tail">
${h.javascript_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.jquery.min.js')}
<script type="text/javascript">
    $(function() {
        $('select[name="remote_id"]').chosen();
        $('.expand-recipients').click(function() {
            $(this).toggleClass('active');
            $(this).parents('tr').next().toggle();
            return false;
        });
    });
</script>
</%block>

<%block name="extra_head">
${h.stylesheet_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.min.css')}
</%block>
