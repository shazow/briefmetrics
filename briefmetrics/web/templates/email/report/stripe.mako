<%inherit file="base.mako"/>
<%namespace file="widgets.mako" name="widgets" />

<p>
    ${widgets.render_intro(
        current=c.report.data['total_current'],
        last=c.report.data['total_last'],
        last_relative=c.report.data['total_last_relative'],
        units=c.report.data['total_units'],
        interval=(c.report.data.get('total_last_date_start', c.report.previous_date_start), c.report.date_start, c.report.date_end),
    )}
</p>

${h.chart(c.report.data['historic_data'], width=560, height=200)}

% if c.report.tables['customers'].rows:
    <h2>New Customers</h2>

    ${c.report.tables['customers'].render_html()}
% else:
    <p>
        No new customers this week.
    </p>
% endif

<h2>Events</h2>
${c.report.tables['events'].render_html()}
