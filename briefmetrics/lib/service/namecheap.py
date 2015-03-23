import time
import datetime

from .base import OAuth2API

from briefmetrics.lib import helpers as h
from briefmetrics.lib.http import assert_response
from unstdlib import get_many


class NamecheapAPI(OAuth2API):
    id = 'namecheap'

    config = {
        'auth_url': 'XXX',
        'token_url': 'XXX',
        'scope': ['read_only'],

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }

    def query_user(self):
        r = self.session.get('XXX')
        r.raise_for_status()
        user_info = r.json()
        return user_info['id'], user_info['email'], user_info.get('display_name'), user_info
