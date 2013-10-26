<%def name="payment_form_body()">
    <div class="payment-errors inline-error"></div>
    <div>
        <label>
            Card Number
            <div>
                <input type="text" size="20" autocomplete="off" class="card-number" data-stripe="number" />
            </div>
        </label>
        <label>
            CVC
            <div>
                <input type="text" size="4" autocomplete="off" class="card-cvc" data-stripe="cvc" />
            </div>
        </label>
    </div>
    <div>
        <label>Month
            <div>
                <input type="text" size="2" class="card-expiry-month" placeholder="MM" data-stripe="exp-month" />
                <span>/</span>
            </div>
        </label>
        <label>Year
            <div>
                <input type="text" size="4" class="card-expiry-year" placeholder="YYYY" data-stripe="exp-year" />
            </div>
        </label>
        <label>
            <input type="submit" class="submit-button" value="Save Card" />
        </label>
    </div>
</%def>


<%def name="payment_form()">
    <form action="${request.route_path('api')}" method="post" class="payment">
        ${payment_form_body(include_submit=True)}

        <input type="hidden" name="csrf_token" value="${session.get_csrf_token()}" />
        <input type="hidden" name="method" value="settings.payments" />
        <input type="hidden" name="format" value="redirect" />
    </form>
</%def>
