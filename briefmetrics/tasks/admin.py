from .setup import celery


@celery.task(ignore_result=True)
def test_errors(message):
    raise Exception(message)
