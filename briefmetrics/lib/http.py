import logging

from requests.exceptions import HTTPError
from briefmetrics.lib.exceptions import APIError


log = logging.getLogger(__name__)


def assert_response(r):
    try:
        r.raise_for_status()
    except HTTPError as e:
        # TODO: Handle case when... {"error":{"errors":[{"domain":"global","reason":"insufficientPermissions","message":"User does not have sufficient permissions for this profile."}],"code":403,"
        log.error("assert_response failure: Request to [%s] returned code [%s]: %s" % (e.response.request.url, e.response.status_code, e.response.text[:200]))

        try:
            error = r.json()['error']
            if isinstance(error, basestring):
                message = error
            elif isinstance(error, dict) and 'errors' in error:
                message = '; '.join(e['message'] for e in error['errors'])
            else:
                message = str(error)

            raise APIError("API call failed: %s" % message, e.response.status_code, response=e.response)
        except (ValueError, KeyError):
            raise APIError("API call failed.", e.response.status_code, response=e.response)
