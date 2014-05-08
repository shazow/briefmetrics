<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">
    % if c.user and c.user.plan.is_hidden and c.user.plan.price_monthly:
        <p>
            You are currently on an unlisted grandfathered plan: 
            <strong>${c.user.plan.name}</strong> at ${c.user.plan.price_str}.
        </p>
    % endif
    <div class="pricing">
        ${forms.pricing_plan(c.plan_individual, user=c.user)}

        ${forms.pricing_plan(c.plan_agency, user=c.user)}

        ${forms.pricing_plan(c.plan_enterprise, user=c.user)}
    </div>
</div>
