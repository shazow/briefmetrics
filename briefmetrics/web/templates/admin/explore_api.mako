<%inherit file="/base.mako" />


<div class="container">
    <form action="${request.route_path('api')}" method="post">
        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="admin.explore_api" />
        <input type="hidden" name="format" value="json" />

        <select name="report_id">
        % for report in c.reports:
            <option value="${report.id}">
                ${report.display_name}
            </option>
        % endfor
        </select>

        <input type="text" name="metrics" placeholder="Metrics" />
        <input type="text" name="dimensions" placeholder="Dimensions" />
        <input type="text" name="extra" value="max-results=10" />

        <input type="submit" />
    </form>
</div>
