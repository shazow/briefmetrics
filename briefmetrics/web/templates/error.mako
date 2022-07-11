<%inherit file="/base.mako"/>

<div class="container">
    <h2>Error</h2>

    % if hasattr(c.exc, 'code'):
    <h4>(Code ${c.exc.code})</h3>
    % endif

    <p>${c.exc}</p>
</div>
