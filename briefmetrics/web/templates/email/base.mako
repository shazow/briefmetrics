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

    body {
        background-color: #f6faee;
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
    }
    p, ul, table {
        margin-top: 0.5em;
        margin-bottom: 1em;
    }
    p {
        line-height: 1.5em;
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
    }
    td.number {
        text-align: right;
        vertical-align: top;
    }

    h2 {
        margin-top: 1.5em;
        font-size: 1em;
    }
    thead td > a, h3 > a {
        background: #ce2342;
        color: #f9e4e8;
        text-decoration: none;
        padding: 1px 3px;
        -webkit-border-radius: 3px;
        -moz-border-radius: 3px;
        border-radius: 3px;
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

<div class="content">
${next.body()}
</div>

</body>

</html>
