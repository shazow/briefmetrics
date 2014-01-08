<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />
<%namespace file="widgets.mako" name="widgets" />

<div class="container">

<section id="plan">
    ${widgets.plan_summary(has_card=c.user.stripe_customer_id, num_remaining=c.user.num_remaining)}
</section>

<section id="new-report">
    <h2>New report</h2>

    ${forms.report_new(c.available_profiles)}
</section>

% if c.reports:
<section id="active-reports">
    <h2>Active reports</h2>

    % for report in sorted(c.reports, key=lambda r: r.display_name):
        ${forms.report_config(report, is_active=c.user.num_remaining == 0 and not c.user.stripe_customer_id, is_admin=c.user.is_admin)}
    % endfor
</section>
% endif

</div>

<%block name="tail">
${h.javascript_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.jquery.min.js')}
<script type="text/javascript">
    $(function() {
        $("select[name=\"remote_id\"]").chosen();
        $("select[name=\"type\"]").chosen({
            ##disable_search: true,
            ##display_selected_options: false
        });
    });
</script>
</%block>

<%block name="extra_head">
${h.stylesheet_link(request, 'briefmetrics.web:static/js/external/chosen/chosen.min.css')}
</%block>
