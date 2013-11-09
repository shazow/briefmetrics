from briefmetrics import test
from briefmetrics import model


Session = model.Session


class TestModel(test.TestModel):
    def test_cascade_delete(self):
        u1 = model.User.create(email=u'foo@example.com')
        u2 = model.User.create(email=u'bar@example.com')
        a = model.Account.create(user=u1)
        r = model.Report.create(account=a)
        model.Subscription.create(user=u1, report=r)
        model.Subscription.create(user=u2, report=r)
        model.ReportLog.create_from_report(r, u'', '')
        Session.commit()

        Session.delete(u1)
        Session.commit()

        self.assertEqual(model.User.count(), 1)
        self.assertEqual(model.Account.count(), 0)
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.Subscription.count(), 0)


    def test_cascade_retain(self):
        u1 = model.User.create(email=u'foo@example.com')
        u2 = model.User.create(email=u'bar@example.com')
        a = model.Account.create(user=u1)
        r = model.Report.create(account=a)
        model.Subscription.create(user=u1, report=r)
        s2 = model.Subscription.create(user=u2, report=r)
        model.ReportLog.create_from_report(r, u'', '')
        Session.commit()

        Session.delete(s2)
        Session.commit()

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Account.count(), 1)
        self.assertEqual(model.Report.count(), 1)
        self.assertEqual(model.Subscription.count(), 1)

        Session.delete(r)
        Session.commit()

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Account.count(), 1)
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.Subscription.count(), 0)
