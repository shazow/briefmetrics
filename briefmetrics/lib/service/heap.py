import requests
import json

from briefmetrics.lib.http import assert_response

COLLECT_URL = 'https://heapanalytics.com/api/track'
COLLECT_SESSION = requests.Session()

def collect(app_id, identity=None, event=None, properties=None, http_session=COLLECT_SESSION):
    """

    $ curl \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{
          "app_id": "1675620903",
          "identity": "alice@example.com",
          "event": "Send Transactional Email",
          "properties": {
            "subject": "Welcome to My App!",
            "variation": "A"
          }
        }' \
        https://heapanalytics.com/api/track

    ref: https://heapanalytics.com/docs/server-side#track
    """
    params = {
        'app_id': app_id
    }

    if identity:
        params['identity'] = identity

    if event:
        params['event'] = event

    if properties:
        params['properties'] = properties

    headers = {'Content-type': 'application/json'}
    req = requests.Request('POST', COLLECT_URL, data=json.dumps(params), headers=headers).prepare()
    resp = http_session.send(req)
    assert_response(resp)
    return resp


def extract(t):
    items = [{
        'amount': line.get('ip'),
        'currency': line.get('cu'),
        'quantity': line.get('iq'),
        'description': line.get('in'),
    } for line in t.get('items', [])]

    return {
        'id': t.get('ti'),
        'total': t.get('tr'),
        'currency': t.get('cu'),
        'items': items,
        'provider': 'stripe',
    }

