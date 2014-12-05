function stripeResponseHandler(status, response) {
    if (response.error) {
        $('.payment-errors', this).show().text(response.error.message);
        $('input[type="submit"]', this).prop('disabled', false);
        $(this).get(0).disabled = false;
    } else {
        $('<input type="hidden" name="stripe_token" />').val(response['id']).appendTo(this);

        var tracker = ga.getAll()[0];
        $('<input type="hidden" name="ga_cid" />').val(tracker.get('clientId')).appendTo(this);

        $(this).get(0).submit();
    }
};


$(document).ready(function() {
    $('form.payment').submit(function(event) {
        if($(this).get(0).disabled) {
            return false;
        } else {
            $(this).get(0).disabled = true;
        }

        $('input[type="submit"]', this).prop('disabled', true);

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

