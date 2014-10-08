<%inherit file="base.mako"/>
<%namespace file="weekly.mako" name="weekly" />

% for r in c.report.contexts:
${weekly.render_weekly(r)}
% endfor
