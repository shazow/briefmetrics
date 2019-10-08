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

        env_test_ini = os.environ.get('INI_FILE', 'test.ini')
        here_dir = os.path.dirname(os.path.abspath(__file__))
        conf_dir = os.path.dirname(os.path.dirname(here_dir))
        test_ini = os.path.join(conf_dir, env_test_ini)

        cls.settings = paste.deploy.appconfig('config:' + test_ini)

    def setUp(self):
        super(TestApp, self).setUp()

        self.config = web.environment.setup_testing(**self.settings)
        self.wsgi_app = self.config.make_wsgi_app()


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
        from pyramid.threadlocal import get_current_request 
        self.app = TestApp(self.wsgi_app)
        self.csrf_token = self.settings['session.constant_csrf_token']
        self.request = get_current_request()
        self.request.registry = self.config.registry
        #self.request.features['offline'] = True

    def call_api(self, method, format='json', csrf_token=_DEFAULT, _status=None, _extra_params=None, _upload_files=None, **params):
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

        r = self.app.post('/api', status=_status, upload_files=_upload_files, params=p, content_type='application/json')

        if format == 'json':
            return json.loads(r.body)

        return r
