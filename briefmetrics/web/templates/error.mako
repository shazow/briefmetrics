<%inherit file="/base.mako"/>

<div class="container">
    <h2>Error</h2>

    <h4>(Code ${c.exc.code})</h3>

    <p>${c.exc.message}</p>
</div>
