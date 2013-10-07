<%inherit file="base.mako"/>

<div class="container">

    <h1>Select a site</h1>

    <form action="${request.current_route_path()}" method="post">

        <ul class="ga-profiles">
        % for item in c.result['items']:
            <%
                subscribe_url = request.route_path(
                    'settings',
                    _query={'profile_id': item['id'], 'method': 'settings.subscribe'},
                )
                human_url = h.human_url(item['websiteUrl']) or item['name']
                name = h.human_url(item['name'])
            %>
            <li>
                <label>
                    <input type="radio" name="id" value="${item['id']}" ${h.text_if(item['id'] in c.report_ids, 'checked="checked"')}/>
                    <span class="property-url">${human_url}</span>
                    % if name not in ['All Web Site Data', human_url]:
                        <strong class="property-name">${name}</strong>
                    % endif
                    <span class="property-id">${item['webPropertyId']}</span>
                </label>
            </li>
        % endfor
        </ul>

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.subscribe" />
        <input type="hidden" name="format" value="redirect" />
        <input type="submit" value="Save Settings" />
    </form>

</div>
