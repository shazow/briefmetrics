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
        padding: 2px 0 2px 0;
    }
    td.number {
        padding-right: 1em;
        text-align: right;
        vertical-align: top;
        width: 4.5em;
    }
    h1 {
        line-height: 1em;
        margin: 0;
        text-align: center;
        padding: 1em 0 1em 0;
    }

    h2 {
        margin-top: 1.5em;
        font-size: 1.5em;
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
        font-size: 2em;
        color: #ffad39;
        display: block;
        line-height: 1em;
        font-weight: normal;
    }
    .overview small{
        color: green;
        display: block;
        font-weight: normal;
    }
    .overview small.neg {
        color: red;
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
    </style>
</head>
<body>

<h1>
    <img src="https://briefmetrics.com/static/images/email_headers/${c.report.owner.config.get('email_header_image', 'briefmetrics.png')}" />
</h1>

<div class="content">

% if c.report.messages:
    % for message in c.report.messages:
        <p>${message}</p>
    % endfor

    <h3>Back to your previously scheduled report...</h3>
% endif

${next.body()}

<div class="footer">
    <p>
        <strong>Please send feedback by replying to this email.</strong>
    </p>
    % if c.report.owner == c.user:
        <p>
            Looking for something different?
            <a href="https://briefmetrics.com/reports">Change subscription</a> &middot;
            <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">Delete account</a>
        </p>
    % else:
        <p>
            You're receiving these emails because ${c.report.owner.display_name} added you as a recipient. 
            If you're not interested, you can <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">unsubscribe here</a>.
        </p>
    % endif
</div>

</div>

</body>

</html>
