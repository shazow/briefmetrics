<%inherit file="base.mako"/>

<div class="container">

<h1>Report</h1>

<ul>
% for item in c.result['items']:
    <li>
        <a href="/settings?profile_id=${item['id']}">${item['webPropertyId']}</a> ${item['websiteUrl']} (${item['name']})
    </li>
% endfor
</ul>

</div>
