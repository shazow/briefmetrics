<%inherit file="base.mako"/>
<%namespace file="weekly.mako" name="weekly" />

% for r in c.report.contexts:
<div class="report">
<h1>${r.display_name}</h1>
${weekly.render_weekly(r)}
</div>
% endfor
