from .setup import celery


@celery.task
def test_errors(message):
    raise Exception(message)
