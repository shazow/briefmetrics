from briefmetrics.lib.service.stripe import Query

class FakeQuery(Query):
    def __init__(self, *args, **kw):
        super(FakeQuery, self).__init__(*args, **kw)

    def get(self, url, params=None):
        return {}

    def validate_webhook(self, webhook_data):
        return webhook_data

    def extract_transaction(self, webhook_data, load_customer=False):
        return Query.extract_transaction(self, webhook_data, load_customer=load_customer)
