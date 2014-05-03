# TODO: Move into a lib submodule
from briefmetrics import test
from briefmetrics.lib import pricing


class TestPricing(test.TestCase):
    def test_new_plans(self):
        class TestPlan(pricing.Plan):
            _singleton = {}


        class TestFeature(pricing.Feature):
            _singleton = {}

        f1 = TestFeature.new('foo', 'Foo')
        f2 = TestFeature.new('baz')

        p1 = TestPlan.new('p1', 'Plan 1', features={
            'foo': 'bar',
            'baz': True,
        })

        p2 = TestPlan.new('p2', 'Plan 2', features=[
            TestFeature.value('foo', 'bar'),
            TestFeature.value('baz', True),
        ])

        self.assertEqual(p1.features, p2.features)
        self.assertEqual(TestPlan.get('p1'), p1)
        self.assertRaises(KeyError, TestPlan.get, 'foo')
        self.assertEqual(TestFeature.get('foo'), f1)
        self.assertRaises(KeyError, TestFeature.get, p1)
