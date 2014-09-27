<%namespace file="/widgets.mako" name="widgets" />
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />

    % if title:
        <title>${title} | Briefmetrics</title>
    % else:
        <title>Briefmetrics - Email Reports For Your Google Analytics</title>
    % endif

    <link rel="icon" type="image/png" href="/static/images/icon_32px.png?5" />
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=Nunito:300,700" />

    ${h.stylesheet_link(request, 'briefmetrics.web:static/css/screen.css')}

    <%block name="extra_head"></%block>

    % if track_analytics:
    <script type="text/javascript">
      window.heap=window.heap||[],heap.load=function(t,e){window.heap.appid=t,window.heap.config=e;var a=document.createElement("script");a.type="text/javascript",a.async=!0,a.src=("https:"===document.location.protocol?"https:":"http:")+"//cdn.heapanalytics.com/js/heap.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(a,n);for(var o=function(t){return function(){heap.push([t].concat(Array.prototype.slice.call(arguments,0)))}},p=["identify","track"],c=0;c<p.length;c++)heap[p[c]]=o(p[c])};
      heap.load("1675620903");
    </script>
    % endif
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
% if not is_logged_in and not current_route == request.route_path('index'):
    <p><a href="/">Briefmetrics</a> emails you weekly summaries of your Google Analytics.
        <a href="${login_url}">Try it now</a> with 10 free emails!
    </p>
% endif
Questions? Send an email to <a href="mailto:support@briefmetrics.com">support@briefmetrics.com</a>
</footer>
</%block>

% if track_analytics:
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  % if request.unauthenticated_userid:
  ga('create', 'UA-407051-16', {'userId': '${request.unauthenticated_userid}'});
  % else:
  ga('create', 'UA-407051-16', 'auto');
  % endif
  ga('require', 'displayfeatures');
  ga('send', 'pageview');

  % if getattr(c, 'user', None):
  heap.identify({
      handle: '${request.unauthenticated_userid}',
      name: '${c.user.display_name}',
      plan: '${c.user.plan_id}',
  });
  % elif request.unauthenticated_userid:
  heap.identify({handle: '${request.unauthenticated_userid}'});
  % endif
</script>

<!-- begin olark code -->
<script data-cfasync="false" type='text/javascript'>/*<![CDATA[*/window.olark||(function(c){var f=window,d=document,l=f.location.protocol=="https:"?"https:":"http:",z=c.name,r="load";var nt=function(){
f[z]=function(){
(a.s=a.s||[]).push(arguments)};var a=f[z]._={
},q=c.methods.length;while(q--){(function(n){f[z][n]=function(){
f[z]("call",n,arguments)}})(c.methods[q])}a.l=c.loader;a.i=nt;a.p={
0:+new Date};a.P=function(u){
a.p[u]=new Date-a.p[0]};function s(){
a.P(r);f[z](r)}f.addEventListener?f.addEventListener(r,s,false):f.attachEvent("on"+r,s);var ld=function(){function p(hd){
hd="head";return["<",hd,"></",hd,"><",i,' onl' + 'oad="var d=',g,";d.getElementsByTagName('head')[0].",j,"(d.",h,"('script')).",k,"='",l,"//",a.l,"'",'"',"></",i,">"].join("")}var i="body",m=d[i];if(!m){
return setTimeout(ld,100)}a.P(1);var j="appendChild",h="createElement",k="src",n=d[h]("div"),v=n[j](d[h](z)),b=d[h]("iframe"),g="document",e="domain",o;n.style.display="none";m.insertBefore(n,m.firstChild).id=z;b.frameBorder="0";b.id=z+"-loader";if(/MSIE[ ]+6/.test(navigator.userAgent)){
b.src="javascript:false"}b.allowTransparency="true";v[j](b);try{
b.contentWindow[g].open()}catch(w){
c[e]=d[e];o="javascript:var d="+g+".open();d.domain='"+d.domain+"';";b[k]=o+"void(0);"}try{
var t=b.contentWindow[g];t.write(p());t.close()}catch(x){
b[k]=o+'d.write("'+p().replace(/"/g,String.fromCharCode(92)+'"')+'");d.close();'}a.P(2)};ld()};nt()})({
loader: "static.olark.com/jsclient/loader0.js",name:"olark",methods:["configure","extend","declare","identify"]});
/* custom configuration goes here (www.olark.com/documentation) */
olark.identify('3884-493-10-9440');/*]]>*/</script><noscript><a href="https://www.olark.com/site/3884-493-10-9440/contact" title="Contact us" target="_blank">Questions? Feedback?</a> powered by <a href="http://www.olark.com?welcome" title="Olark live chat software">Olark live chat software</a></noscript>
<!-- end olark code -->
% endif

% if is_logged_in:
    <script src="//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
    <script>!window.jQuery && document.write(unescape('%3Cscript src="/static/js/external/jquery.min.js"%3E%3C/script%3E'))</script>
    ${h.javascript_link(request, 'briefmetrics.web:static/js/core.js')}
% endif

<%block name="tail"></%block>

</body>

</html>
