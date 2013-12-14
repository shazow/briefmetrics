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
        color: #25ad83;
    }
    a.highlight {
        background: #c6eadf;
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
        background: #ecfadd;
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
        background: #beeee1;
        padding: 1px 2px;
    }
    .chartBottom {
        background: #fce09b;
        padding: 1px 2px;
    }
    .done {
        text-decoration: line-through;
        color: #888;
    }
    a.permalink {
        float: right;
        color: #9db883;
        line-height: 2em;
        font-size: 0.8em;
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
    .quiet {
        font-size: 0.8em;
        color: #999;
        font-weight: normal;
    }
    .optional-inverse {
        display: none;
    }

    .tag {
        background: #eee;
        white-space: nowrap;
        padding: 1px 3px;
        margin-right: 0.5em;
    }

    .bubble {
        font-size: 11px;
    }
    .bubble.positive {
        color: #5FA81B;
    }
    .bubble.negative {
        color: #ae2e3e;
    }

    .engagement {
        cursor: default;
        border-radius: 3px;
        background: #eee;
        color: #999;
        padding: 0px 4px;
        white-space: nowrap;
    }
    .engagement.positive {
        background: #ecfadd;
        color: #91AD77;
    }
    .engagement.negative {
        background: #e8d9da;
        color: #B88D8B;
    }

    .label {
        text-transform: uppercase;
        font-weight: bold;
        font-size: 9px;
        letter-spacing: 0.5px;
    }
    </style>
</head>
<body>

<h1>
    <img src="https://briefmetrics.com/static/images/email_logo.png" />
</h1>

<div class="content">
${next.body()}
</div>

</body>

</html>
