<%inherit file="base.mako"/>

<div class="container">

<h1>Report</h1>

<ul>
% for row in c.result['rows']:
    <li>
        ${repr(row)}
    </li>
% endfor
</ul>

</div>
