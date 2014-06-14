from briefmetrics import test
from briefmetrics import api
from briefmetrics import model


Session = model.Session

class TestAccount(test.TestWeb):
    def test_get_account(self):
        user, account = api.account.get_account(self.request)
        self.assertEqual(user, None)
        self.assertEqual(account, None)

        u = api.account.get_or_create(email=u'example@example.com', display_name=u'Example')
        api.account.login_user_id(self.request, u.id)

        user, account = api.account.get_account(self.request)
        self.assertNotEqual(user, None)
        self.assertNotEqual(account, None)
