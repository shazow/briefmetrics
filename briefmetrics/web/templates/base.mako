<%namespace file="/widgets.mako" name="widgets" />
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />

    % if title:
        <title>${title} | Briefmetrics</title>
    % else:
        <title>Briefmetrics</title>
    % endif

    <link rel="icon" type="image/png" href="/static/images/icon_32px.png" />
    ${h.stylesheet_link(request, 'briefmetrics.web:static/css/screen.css')}

    <%block name="extra_head"></%block>
</head>

<body>


<%block name="header">
% if is_logged_in:
    Welcome. (<A href="${request.route_path('account_logout')}">Log out</a>)
% else:
    <A href="${request.route_path('account_login')}">Sign in</a>?
% endif
</%block>


<div class="content">
${widgets.flash_messages(request.session.pop_flash())}

${next.body()}
</div>

<%block name="footer">
    <footer>Questions? <a href="mailto:support@briefmetrics.com">support@briefmetrics.com</a></footer>
</%block>

<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-407051-16', 'briefmetrics.com');
  ga('send', 'pageview');
</script>

<%block name="tail"></%block>

</body>

</html>