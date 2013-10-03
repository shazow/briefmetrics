<%inherit file="base.mako"/>

<div class="container">

<h1>Report</h1>

<ul>
% for item in c.result['items']:
    <li>
        ${repr(item)}
    </li>
% endfor
</ul>

</div>
