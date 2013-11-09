import logging

from requests.exceptions import HTTPError
from briefmetrics.lib.exceptions import APIError


log = logging.getLogger(__name__)


def assert_response(r):
    try:
        r.raise_for_status()
    except HTTPError as e:
        log.error("assert_response failure: Request to [%s] returned code [%s]: %s" % (e.response.request.url, e.response.status_code, e.response.text[:200]))
        raise APIError("API call failed.", e.response.status_code, response=e.response)
