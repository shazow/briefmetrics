<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width"> 
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <style type="text/css">
    h1, h2, h3, h4, h5 {
        font-weight: normal;
        font-size: 21px;
        color: #000;
    }
    h1 {
        letter-spacing: 0.5px;
        line-height: 1em;
        margin: 0;
        text-align: center;
        padding: 1em 0 1em 0;
        color: #bbb;
    }
    h2 {
        margin-top: 1.5em;
        font-size: 1.5em;
    }

    .content {
        background-color: #fff;
        max-width: 560px;
        margin: 0 auto;
    }

    body {
        font: 15px/1.6 Arial, sans-serif;
        color: #666;
    }
    .todo {
        font-size: 0.8em;
        background: #eee;
        color: #bbb;
        display: block;
        padding: 0.3em;
        margin: 1em 0;
    }

    a {
        text-decoration: none;
        color: ${c.report.owner.config.get('style_a_color', '#25ad83')};
    }
    a.highlight {
        background: #c6eadf;
    }
    a.permalink {
        float: right;
        color: ${c.report.owner.config.get('style_permalink_color', '#9db883')};
        line-height: 2em;
        font-size: 0.8em;
        padding-right: 0.5em;
    }
    p, ul, table {
        margin-top: 0.5em;
        margin-bottom: 1.5em;
    }
    p {
        line-height: 1.5em;
    }
    table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 0.9em;
    }
    thead {
        background: ${c.report.owner.config.get('style_thead_background', '#ecfadd')};
        color: #000;
        font-weight: bold;
        font-size: 0.8em;
        text-transform: uppercase;
    }
    thead .number {
        color: #526440;
    }
    tbody {
        font-size: 0.9em;
    }
    td {
        padding: 2px 4px 2px 4px;
    }
    td.arrow {
        width: 1px;
        color: #ffd69b;
        vertical-align: top;
        line-height: 2em;
    }
    td.number {
        padding-right: 0.5em;
        text-align: right;
        vertical-align: top;
        width: 5.5em;
    }
    td.date {
        color: #999;
        width: 6em;
        vertical-align: top;
        text-align: right;
    }
    td.alt,tr.alt {
        background: #f5f5f5;
    }

    .highlight {
        background: #fce09b;
        padding: 1px 2px;
    }
    .chartTop {
        white-space: nowrap;
        background: #beeee1;
        padding: 1px 2px;
    }
    .chartBottom {
        white-space: nowrap;
        background: #fce09b;
        padding: 1px 2px;
    }
    .done {
        text-decoration: line-through;
        color: #888;
    }
    .overview {
        font-size: 1em;
        text-align: center;
        font-weight: bold;
    }
    .overview strong {
        font-size: 1.8em;
        color: #ffad39;
        display: block;
        line-height: 1em;
        font-weight: normal;
    }
    .overview small {
        color: #999;
        display: block;
        font-weight: normal;
    }
    .overview small.neg {
        color: red;
    }
    .overview small.pos {
        color: green;
    }

    .footer {
        border-top: 1px solid #ddd;
        padding-top: 1em;
        margin-top: 1em;
        color: #666;
        font-size: 0.8em;
    }
    .footer p {
        line-height: 1.2em;
        margin-bottom: 0.5em;
    }
    .quiet {
        font-size: 0.8em;
        color: #999;
        font-weight: normal;
    }
    .optional-inverse {
        display: none;
    }

    .annotation {
        border-radius: 3px;
        background: #eee;
        color: #999;
        padding: 2px 4px;
        white-space: nowrap;
        margin-right: 3px;
        font-size: 10px;
    }
    .label {
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 0.5px;
        margin: 0 2px;
    }
    .annotation.positive {
        background: #ecfadd;
        color: #91AD77;
    }
    .annotation.negative {
        background: #F6E8E9;
        color: #B88D8B;
    }

    .preview {
        text-align: center;
        font-size: 0.8em;
        color: #999;
    }
    .report {
        margin-bottom: 1.5em;
        padding-bottom: 2em;
        border-bottom: 1px solid #ddd;
    }
    </style>
</head>
<body>

<%
    preview_text = c.report.get_preview()
    email_header_image = c.report.owner.config.get('email_header_image', 'briefmetrics.png')
    email_intro_text = c.report.owner.config.get('email_intro_text')
%>

% if preview_text:
<p class="preview">${preview_text}</p>
% endif

<h1>
    <img src="https://briefmetrics.com/static/images/email_headers/${email_header_image}" />
</h1>

<div class="content">

% if email_intro_text:
    <p class="intro">${h.literal(email_intro_text)}</p>
% endif

% if c.report.messages:
    % for message in c.report.messages:
        <p>${message}</p>
    % endfor

    <h3>Back to your previously scheduled report...</h3>
% endif

${next.body()}

<p>
    % if c.report.owner.num_remaining is None or c.report.owner != c.user:
        You can look forward to your next report on <span class="highlight">${h.human_date(c.report.date_next)}</span>.
    % elif c.report.owner.payment:
        % if c.report.owner.payment.is_charging and c.report.owner.num_remaining > 1:
            You have <span class="highlight">${c.report.owner.num_remaining-1} free reports</span> remaining before your paid subscription begins.
            Your next report is scheduled for ${h.human_date(c.report.date_next)}.
        % elif c.report.owner.num_remaining > 1:
            You have <span class="highlight">${c.report.owner.num_remaining-1} free reports</span> remaining in your trial. 
            <a href="https://briefmetrics.com/settings">Activate your paid subscription</a> to continue receiving reports.
            Your next report is scheduled for ${h.human_date(c.report.date_next)}.
        % elif c.report.owner.payment.is_charging and c.report.owner.num_remaining <= 1:
            This is your final free report. Your paid subscription will begin after this report.
        % elif c.report.owner.num_remaining <= 1:
            <strong>This is your final report. :(</strong><br />
            Please <a href="https://briefmetrics.com/settings">activate your paid subscription</a> to continue receiving Briefmetrics reports.
        % endif
    % elif c.report.owner.num_remaining <= 1:
        <strong>This is your final report. :(</strong><br />
        Please <a href="https://briefmetrics.com/settings">add a credit card now</a> to continue receiving Briefmetrics reports.
    % elif c.report.owner.num_remaining > 1:
        <strong>You have <span class="highlight">${c.report.owner.num_remaining-1} free reports</span> remaining.</strong>
        <a href="https://briefmetrics.com/settings">Add a credit card now</a> to
        upgrade your account.
        Your next report is scheduled for ${h.human_date(c.report.date_next)}.
    % endif
</p>

<div class="footer">
    <%
        prepared_name = c.user.config.get('prepared_name') or c.user.config.get('from_name')
        if not prepared_name and c.report.owner != c.user:
            prepared_name = c.report.owner.display_name
    %>
    <p style="margin-bottom: 2em;">
        This report was prepared for ${c.user.display_name or 'you'} by
        % if prepared_name:
        <strong>${
            h.human_link(
                c.user.config.get('from_link'),
                prepared_name,
            )}</strong>, and generated by
        % endif
        <a href="https://briefmetrics.com">Briefmetrics</a>.
    </p>

    <p>
        <strong>Please send feedback by replying to this email.</strong>
    </p>

    % if c.report.owner == c.user:
        <p>
            You can <a href="https://briefmetrics.com/reports">change your subscription</a> or
            <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">delete your account</a>.
        </p>
    % else:
        <p>
            You can <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">unsubscribe here</a>.
        </p>
    % endif
</div>

</div>

</body>

</html>
