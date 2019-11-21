<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">
    <h2>Plans &amp Pricing</h2>
    <p>
        Briefmetrics pricing tiers are carefully designed to scale with your
        business while remaining affordable. <strong>Every plan comes
        with a free trial of 10 emails,</strong> no credit card required.
    </p>

    % if c.user and c.user.plan.is_hidden and c.user.plan.price_monthly:
        <p>
            You are currently on an unlisted grandfathered plan: 
            <strong>${c.user.plan.name}</strong> at ${c.user.plan.price_str}.
        </p>
    % endif

    <div class="pricing">

        % if len(c.plans) > 1:
        <div class="toggle">
            <select onchange="toggle(this)">
                % for id, description, _ in c.plans:
                <option value="${id}">${description}</option>
                % endfor
            </select>
        </div>
        % endif

        % for i, (id, _, plans) in enumerate(c.plans):
        <div class="plans" id="${id}" ${h.text_if(i>0, 'style="display: none;"')}>
            % for plan in plans:
            <div class="plan">
                ${forms.pricing_plan(plan, user=c.user)}
            </div>
            % endfor
        </div>
        % endfor
    </div>

    <div id="faq">
        <ul class="questions">
            <li>
                <h3>Can I pay with something other than a credit card?</h3>
                <p>
                    Yes. We accept check or wire transfer payments for 12 month service
                    periods. <a href="mailto:support@briefmetrics.com">Send us an email</a>
                    to arrange payment.
                </p>
            </li>

            <li>
                <h3>What counts as an email for the trial?</h3>
                <p>
                    Whenever you create a report for a website you own, you'll receive
                    weekly email reports for your website. Each of these counts towards
                    your 10 email trial.
                </p>
            </li>

            <li>
                <h3>How much does the Agency plan cost for more than 10 websites?</h3>
                <p>
                    The agency tier cost scales based on your number of clients. Our Agency plan grows up to 50
                    websites, at $3/website/month. <a href="/features/custom-branding-for-agencies">Read more about Briefmetrics for Agencies</a>.
                </p>
            </li>

            <li>
                <h3>Can I use Briefmetrics for more than 50 websites?</h3>
                <p>Yes, <a href="mailto:support@briefmetrics.com">send us an email</a> and we'll work out a plan that works for your business.</p>
            </li>
        </ul>
    </div>

    <div class="closer">
        <p>
            If you have any other questions or need something special for your business,</br >
            please <a href="mailto:support@briefmetrics.com">send us an email</a> and we'll find a way to work together.
        </p>
    </div>
</div>


<%block name="tail">
<script type="text/javascript">
    function toggle(s) {
        var plans = document.getElementsByClassName("plans");
        for (var i=0; i<plans.length; i++) {
            var style = "none";
            if (plans[i].id == s.value) style = "table";
            plans[i].style.display = style;
        }
    };
</script>
</%block>
