import requests
import json
import logging

from briefmetrics.lib.controller import Controller
from briefmetrics.lib.http import assert_response

log = logging.getLogger(__name__)

http_session = requests.session()

API_URL = 'https://mandrillapp.com/api/1.0/'


def render(request, template, context=None):
    return Controller(request, context=context)._render_template(template)


def create_message(request, to_email, subject, html=None, text=None, from_name=None, from_email=None, reply_to=None, debug_bcc=None):
    settings = request.registry.settings
    from_name = from_name or settings['mail.from_name']
    from_email = from_email or settings['mail.from_email']

    message = {
        'from_name': from_name,
        'from_email': from_email,
        'to': [{
            'email': to_email,
        }],
        'subject': subject,
        'track_opens': True,
        'track_clicks': False,
        'auto_text': True,
        'inline_css': True,
    }

    if reply_to:
        message['headers'] = {
            'Reply-To': reply_to,
        }

    if html is not None:
        message['html'] = html
    if text is not None:
        message['text'] = text

    if debug_bcc or debug_bcc is None:
        debug_bcc = settings.get('mail.debug_bcc')

    if debug_bcc:
        message['bcc_address'] = debug_bcc

    return message


def send_message(request, message):
    params = {
        'key': request.registry.settings['api.mandrill.key'],
        'async': True,
        'message': message,
    }

    headers = {'content-type': 'application/json'}
    r = http_session.post(API_URL + 'messages/send.json', data=json.dumps(params), headers=headers)
    assert_response(r)

    return r.json()


def notify_admin(request, subject, text=''):
    if request.registry.settings.get('mail.enabled', 'false') == 'false':
        log.info('Skipping notify_admin: %s' % subject)
        return

    message = create_message(
        request,
        to_email='admin@briefmetrics.com',
        subject='[Briefmetrics] %s' % subject,
        text=text,
    )

    return send_message(request, message)
