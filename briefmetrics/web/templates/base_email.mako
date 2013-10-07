<!DOCTYPE html>
<html lang="en">
<head>
    <title>${c.subject}</title>
    <meta charset="utf-8" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <style type="text/css">
    body {
        color: #444;
        font-family: sans-serif;
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
        padding: 1px 3px;
        color: #33230b;
        -webkit-border-radius: 3px;
        -moz-border-radius: 3px;
        border-radius: 3px;
    }
    .chartTop {
        background: #e38192;
        padding: 1px 3px;
        color: #190408;
        -webkit-border-radius: 3px;
        -moz-border-radius: 3px;
        border-radius: 3px;
    }
    .chartBottom {
        background: #f5d3d9;
        padding: 1px 3px;
        color: #33230b;
        -webkit-border-radius: 3px;
        -moz-border-radius: 3px;
        border-radius: 3px;
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
    </style>
</head>
<body>

${next.body()}

</body>

</html>
