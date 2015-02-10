<%inherit file="base.mako"/>
<%namespace file="weekly.mako" name="weekly" />

% for r in c.report.contexts:
<div class="report">
<h1>${r.display_name}</h1>
% if r.data:
    ${weekly.render_weekly(r)}
% else:
    <em>Insufficient data for this site. Will try again with future reports.</em>
% endif
</div>
% endfor
