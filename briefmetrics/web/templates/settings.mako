<%inherit file="base.mako"/>

<div class="container">

    <h2>Select a site</h2>

    <form action="${request.current_route_path()}" method="post">

        <p>
            <select name="id">
                <option value="">- Select a site</option>
            % for item in c.result['items']:
                <%
                    subscribe_url = request.route_path(
                        'settings',
                        _query={'profile_id': item['id'], 'method': 'settings.subscribe'},
                    )
                    human_url = h.human_url(item['websiteUrl']) or item['name']
                    name = h.human_url(item['name'])
                %>
                <option value="${item['id']}" ${h.text_if(item['id'] in c.report_ids, 'selected="selected"')}>
                    ${human_url}
                    % if name not in ['All Web Site Data', human_url]:
                    ${name}
                    % endif
                    [${item['webPropertyId']}]
                </option>
            % endfor
            </select>
        </p>

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.subscribe" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Save Settings" />
    </form>

</div>

<%block name="tail">
${h.javascript_link(request, 'briefmetrics.web:static/js/core.js')}

<script type="text/javascript" src="https://js.stripe.com/v2/"></script>
<script type="text/javascript">
    Stripe.setPublishableKey('${settings["stripe.public_key"]}');
</script>
</%block>
