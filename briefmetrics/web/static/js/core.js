function stripeResponseHandler(status, response) {
    if (response.error) {
        $('.payment-errors', this).show().text(response.error.message);
        $('.submit-button', this).prop('disabled', false);
    } else {
        var stripeToken = $('<input type="hidden" name="stripe_token" />').val(response['id']);
        $(this).append(stripeToken);
        $(this).get(0).submit();
    }
};


$(document).ready(function() {
    $('form.payment').submit(function(event) {
        // Is it actually a payment form?
        if (!$('.card-number', this).get(0)) {
            return true;
        }
        $('.submit-button', this).prop('disabled', true);

        var form = $(this);
        var callback = function(status, response) {
            stripeResponseHandler.call(form, status, response);
        };

        Stripe.card.createToken(form, callback);

        return false;
    });
});


function inlineError(target, error) {
    if (!error) {
        error = 'An unexpected error occured. Please contact support@introhire.com if it persists.';
    }

    var errorContainer = $('.inline-error', target).hide();
    if (!errorContainer.get(0)) {
        errorContainer = $('<div class="inline-error"></div>').hide().prependTo(target);
    }

    errorContainer.text(error).fadeIn();
};

