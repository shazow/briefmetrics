<%inherit file="base.mako"/>
<%namespace file="forms.mako" name="forms" />

<div class="container">
    <h2>Pricing</h2>

    <div class="pricing">
        ${forms.pricing_plan(c.plan_personal, user=c.user)}

        ${forms.pricing_plan(c.plan_agency, override_name='Agency', is_group=True, user=c.user)}

        ${forms.pricing_plan(c.plan_enterprise, is_group=True, user=c.user)}
    </div>
</div>
