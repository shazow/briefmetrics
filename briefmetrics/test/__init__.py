import json

from unittest import TestCase

from briefmetrics import model
from briefmetrics import web

_DEFAULT = object()


class TestApp(TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        import paste.deploy

        env_test_ini = os.environ.get('TEST_INI', 'test.ini')
        here_dir = os.path.dirname(os.path.abspath(__file__))
        conf_dir = os.path.dirname(os.path.dirname(here_dir))
        test_ini = os.path.join(conf_dir, env_test_ini)

        cls.settings = paste.deploy.appconfig('config:' + test_ini)

    def setUp(self):
        super(TestApp, self).setUp()

        self.config = web.environment.setup_testing(**self.settings)
        self.wsgi_app = self.config.make_wsgi_app()

    def tearDown(self):
        super(TestCase, self).tearDown()
        #testing.tearDown()


class TestModel(TestApp):
    def setUp(self):
        super(TestModel, self).setUp()
        model.create_all()


    def tearDown(self):
        model.Session.remove()


class TestWeb(TestModel):
    def setUp(self):
        super(TestWeb, self).setUp()

        from webtest import TestApp
        self.app = TestApp(self.wsgi_app)
        self.csrf_token = self.settings['session.constant_csrf_token']
        self.request = web.environment.Request.blank('/')

    def call_api(self, method, format='json', csrf_token=_DEFAULT, _status=None, _extra_params=None, **params):
        if csrf_token is _DEFAULT:
            csrf_token = self.csrf_token

        p = {
            'method': method,
            'csrf_token': csrf_token,
            'format': format,
        }
        p.update(params)
        if _extra_params:
            p.update(_extra_params)

        r = self.app.post('/api', params=p, status=_status)

        return json.loads(r.body)


