<%inherit file="base.mako"/>

<div class="container">
    <h2>Signing in</h2>

    <p id="msg">Processing auth token...</p>
</div>

<script src="//ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
<script>!window.jQuery && document.write(unescape('%3Cscript src="/static/js/external/jquery.min.js"%3E%3C/script%3E'))</script>

<script type="text/javascript">
    function msg(s) {
        document.getElementById("msg").innerHTML = s;
    };

    function result(data, status) {
        if (data["messages"] !== undefined) {
            msg(data["messages"].join("<br />"));
        }
        if (data["result"] && data["result"]["redirect"]) {
            window.location.pathname =  data["result"]["redirect"];
        }
    };

    function sendHash(payload) {
        msg("Validating auth token...");

        var params = {
            "payload": payload,
            "service": "${c.service}",
            "csrf_token": "${session.get_csrf_token()}",
            "method": "account.connect",
            "format": "json"
        }
        $.ajax({
            type: "POST",
            url: "/api",
            data: params,
            dataType: "json",
            success: result,
            error: function(xhr, status, err) {
                msg("Failed to sign in: " + err);
            }
        });
    };

    if (!window.location.hash) {
        msg("Error: Missing auth token.");
    } else {
        $(function() {
            sendHash(window.location.hash.substr(1))
        });
    }
</script>
