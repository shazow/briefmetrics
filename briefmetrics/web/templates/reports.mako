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

% if c.reports:
<section id="active-reports">
    <h2>Active reports</h2>

    % for site in c.sites:
        ${forms.site_config(
            site,
            is_active=c.user.num_remaining != 0 or c.user.stripe_customer_id,
            is_admin=c.user.is_admin,
        )}
    % endfor
</section>
% endif

<!--
${c.user.display_name}
${c.get('user') and c.get('user').display_name}
${c.keys()}
-->

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
