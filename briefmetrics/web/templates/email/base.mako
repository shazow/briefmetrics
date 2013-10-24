<!DOCTYPE html>
<html lang="en">
<head>
    <title>${c.subject}</title>
    <meta charset="utf-8" />
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
        padding: 10px 20px;
        border-radius: 5px;
    }

    @media only screen and (max-device-width: 600px) {
        .content {
            padding: 5px 10px; !important
        }
    }

    body {
        background-color: #ecfadd;
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
    p, ul, table {
        margin-top: 0.5em;
        margin-bottom: 1em;
    }
    p {
        line-height: 1.5em;
    }
    table {
        width: 100%;
        table-layout: fixed;
        font-size: 0.9em;
    }
    thead, h3 {
        color: #000;
        font-weight: bold;
        font-size: 0.8em;
        text-transform: uppercase;
    }
    tbody {
        font-family: serif;
    }
    td {
        padding-right: 1em;
        overflow: hidden;
        white-space: nowrap;
    }
    td.number {
        text-align: right;
        vertical-align: top;
        width: 3.5em;
    }
    h1 {
        margin: 0;
        text-align: center;
        padding: 1em 0 1em 0;
    }

    h2 {
        margin-top: 1.5em;
        font-size: 1em;
    }

    .highlight {
        background: #ffad39;
        padding: 1px 2px;
        color: #33230b;
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
        background: #ecfadd;
        color: #9db883;
        line-height: 1em;
        padding: 3px 6px;
        font-size: 0.8em;
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
    </style>
</head>
<body>

<h1>
    <img src="${request.static_url('briefmetrics.web:static/images/email_logo.png')}" />
</h1>

<div class="content">
${next.body()}
</div>

</body>

</html>
