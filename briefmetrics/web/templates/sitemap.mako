<?xml version="1.0" encoding="UTF-8"?>
<%
    urlset = [
        "/",
        "/features",
        "/pricing",
        "/about",
        "/privacy",
        "/terms",
        "/security",
        "/features/custom-branding-for-agencies",
        "/articles/remove-localhost-from-referrers",
    ]
%>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
% for loc in urlset:
    <url>
        <loc>https://briefmetrics.com${loc}</loc>
    </url>
% endfor
</urlset>
