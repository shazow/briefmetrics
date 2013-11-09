<%namespace file="/widgets.mako" name="widgets" />
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    % if title:
        <title>${title} | Briefmetrics</title>
    % else:
        <title>Briefmetrics - Easy to understand Google Analytics reports in your inbox</title>
    % endif

    <link rel="icon" type="image/png" href="/static/images/icon_32px.png?5" />
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Nunito:300,700" />

    ${h.stylesheet_link(request, 'briefmetrics.web:static/css/screen.css')}

    <%block name="extra_head"></%block>
</head>

<body>


<%block name="header">
<%
    nav = [
        #('Pricing', '#', ''),
        #('About', '#', ''),
    ]

    if is_logged_in:
        nav += [
            ('Reports', request.route_path('reports')),
            ('Settings', request.route_path('settings')),
            ('Log out', request.route_path('account_logout')),
        ]

    current_route = request.current_route_path()
%>
<nav class="header">
    <ul>
        <li class="logo">
            <h1><a href="/">Briefmetrics</a></h1>
        </li>
        % for label, href in nav:
            % if current_route == href:
        <li class="menu active">
            % else:
        <li class="menu">
            % endif
            <a href="${href}">${label}</a>
        </li>
        % endfor
    </ul>
</nav>
</%block>


<div class="content">
${widgets.flash_messages(request.session.pop_flash() + request.pop_flash())}

${next.body()}
</div>

<%block name="footer">
<footer>
Questions? Send an email to <a href="mailto:support@briefmetrics.com">support@briefmetrics.com</a>
</footer>
</%block>

% if not request.features.get('offline'):
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-407051-16', 'briefmetrics.com');
  ga('send', 'pageview');
</script>
% endif

% if is_logged_in:
<script src="//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
${h.javascript_link(request, 'briefmetrics.web:static/js/core.js')}
% endif

<%block name="tail"></%block>

</body>

</html>
