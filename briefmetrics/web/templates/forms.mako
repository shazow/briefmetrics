<%def name="payment_form_body()">
    <div class="payment-errors inline-error"></div>
    <div>
        <label>
            Card Number
            <div>
                <input type="text" size="20" autocomplete="off" class="card-number" data-stripe="number" autocompletetype="cc-number" required />
            </div>
        </label>
        <label>
            CVC
            <div>
                <input type="text" size="4" autocomplete="off" class="card-cvc" data-stripe="cvc" autocomplete="off" required />
            </div>
        </label>
    </div>
    <div>
        <label>Month
            <div>
                <input type="text" size="2" class="card-date card-expiry-month" placeholder="MM" data-stripe="exp-month" autocompletetype="cc-month" required />
                <span class="card-expiry-sep">/</span>
            </div>
        </label>
        <label>Year
            <div>
                <input type="text" size="4" class="card-date card-expiry-year" placeholder="YYYY" data-stripe="exp-year" autocompletetype="cc-year" required />
            </div>
        </label>
        <label>
            <input type="submit" class="submit-button" value="Start Plan" />
        </label>
    </div>
</%def>


<%def name="payment_form()">
    <form action="${request.route_path('api')}" method="post" class="payment" autocomplete="on">
        <div>
            <label>
                Plan
                <div>
                    <%
                        plans = [p for p in pricing.PLANS if not p.is_hidden]
                    %>
                    % if len(plans) == 1:
                        <input type="hidden" name="plan_id" value="${plans[0].id}" />
                        <strong>
                            ${plans[0].option_str}
                        </strong>
                    % else:
                        <select name="plan_id">
                        % for plan in plans:
                            <option value="${plan.id}">
                                ${plan.option_str}
                            </option>
                        % endfor
                        </select>
                    % endif
                </div>
            </label>
        </div>

        ${payment_form_body()}

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.payments" />
        <input type="hidden" name="format" value="redirect" />
    </form>
</%def>
