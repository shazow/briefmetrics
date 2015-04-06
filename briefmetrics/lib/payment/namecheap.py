from .base import Payment, PaymentError


class NamecheapPayment(Payment):
    id = "namecheap"

    def set(self, new_token=None, metadata=None):
        if new_token:
            self.user.set_payment('namecheap', new_token)

    def start(self):
        if not self.token:
            raise PaymentError("Cannot start subscription for user without a payment method: %s" % self.user.id)

        if not self.plan_id:
            raise PaymentError("Cannot start subscription for user without a confirmed plan: %s" % self.user.id)

        # TODO: Issue payment
        # TODO: Set self.user.time_next_payment

    def delete(self):
        p = self.user.payment
        if not p:
            # Nothing to delete
            return

        assert p.id == 'namecheap'

        # TODO: Remove subscription?
        # TODO: Issue pro-rated refund?
