import requests
import json
import logging
import premailer

from briefmetrics.lib.controller import Controller
from briefmetrics.lib.http import assert_response

log = logging.getLogger(__name__)

http_session = requests.session()


def render(request, template, context=None):
    return Controller(request, context=context)._render_template(template)


def prepare_html(html, inline_css=True):
    if inline_css:
        html = premailer.Premailer(html).transform()
    return html


def create_message(request, to_email, subject, html=None, text=None, from_name=None, from_email=None, reply_to=None, debug_bcc=None, inline_css=True):
    MsgClass = DefaultMessage
    if request.features.get('mailer') == 'mailgun':
        MsgClass = MailgunMessage
    return MsgClass(request, to_email, subject, html=html, text=text, from_name=from_name, from_email=from_email, reply_to=reply_to, debug_bcc=debug_bcc, inline_css=inline_css)


def send_message(request, message, settings=None):
    return message.send(settings=settings)


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


class MandrillMessage(object):
    def __init__(self, request, to_email, subject, html=None, text=None, from_name=None, from_email=None, reply_to=None, debug_bcc=None, inline_css=True):
        self.request = request

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
        }

        if html:
            html = prepare_html(html, inline_css=inline_css)

        if not inline_css:
            message['inline_css'] = True

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

        self.params = message

    def send(self, settings=None):
        settings = settings or self.request.registry.settings
        params = {
            'key': settings['api.mandrill.key'],
            'async': True,
            'message': self.params,
        }

        headers = {'content-type': 'application/json'}
        r = http_session.post('https://mandrillapp.com/api/1.0/messages/send.json', data=json.dumps(params), headers=headers)
        assert_response(r)

        return r.json()



class MailgunMessage(object):
    def __init__(self, request, to_email, subject, html=None, text=None, from_name=None, from_email=None, reply_to=None, debug_bcc=None, inline_css=True):
        self.request = request

        settings = request.registry.settings
        from_name = from_name or settings['mail.from_name']
        from_email = from_email or settings['mail.from_email']

        params = {
            'from': "{from_name} <{from_email}>".format(from_name=from_name, from_email=from_email),
            'to': to_email,
            'subject': subject,
        }

        if html:
            html = prepare_html(html, inline_css=inline_css)

        if reply_to:
            params['h:Reply-To'] = reply_to

        if html is not None:
            params['html'] = html

        if text is not None:
            params['text'] = text

        if debug_bcc or debug_bcc is None:
            debug_bcc = settings.get('mail.debug_bcc')

        if debug_bcc:
            params['bcc'] = debug_bcc

        self.params = params

    def send(self, settings=None):
        api_key = settings['api.mailgun.key']
        api_url = settings.get('api.mailgun.url', 'https://api.mailgun.net/v3/mg.briefmetrics.com')
        r = requests.post(
            api_url + '/messages',
            auth=('api', api_key),
            data=self.params,
        )

        return r.json()

DefaultMessage = MandrillMessage
