# hi
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()

setup(name='briefmetrics',
      version='0.0',
      description='briefmetrics',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='briefmetrics',
      entry_points = """\
      [paste.app_factory]
      main = briefmetrics.web.environment:setup_wsgi
      """,
      paster_plugins=['pyramid'],
      )
