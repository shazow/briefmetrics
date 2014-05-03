<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">
    <div class="pricing">
        ${forms.pricing_plan(c.plan_individual, user=c.user)}

        ${forms.pricing_plan(c.plan_agency, user=c.user)}

        ${forms.pricing_plan(c.plan_enterprise, user=c.user)}
    </div>
</div>
