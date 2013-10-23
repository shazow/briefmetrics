import requests
import json


http_session = requests.session()

API_URL = 'https://mandrillapp.com/api/1.0/'


def create_message(request, to_email, subject, html):
    settings = request.registry.settings
    message = {
        'from_name': settings['mail.from_name'],
        'from_email': settings['mail.from_email'],
        'to': [{
            'email': to_email,
        }],
        'subject': subject,
        'html': html,
        'track_opens': True,
        'track_clicks': True,
        'auto_text': True,
        'inline_css': True,
    }

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
    r.raise_for_status()

    return r.json()
