import time
from .setup import celery

_started = time.time()

@celery.task(ignore_result=True)
def test_errors(message):
    msg = "_started = %f\n\nOriginal message: %s" % (_started, message)
    raise Exception(msg)
