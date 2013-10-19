from celery.utils.log import get_task_logger

from briefmetrics import model
from briefmetrics import api

from .setup import celery


logger = get_task_logger(__name__)


@celery.task
def send_weekly(report_id):
    report = model.Report.get(report_id)
    if not report:
        logger.warn('Invalid report id: %s' % report_id)
        return

    api.report.send_weekly(celery.request, report)
