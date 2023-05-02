import requests

from ecom.logger import logger
from ecommerce.settings import IS_TEST, HOST
from maib_gateway.constants import MAIB_LIVE_BASE_URI, MAIB_TEST_BASE_URI, MAIB_TEST_CERT_KEY_URL, \
    MAIB_TEST_REDIRECT_URL, MAIB_LIVE_REDIRECT_URL


class MaibClient:
    def __init__(self):
        # TODO✓: Figure out how to make SSL request in Python (maybe use something else other than requests)
        # ✓ pahodu merge
        self.default_request_args = {
            'cert': ('api/cert/cert.pem', 'api/cert/key.pem'),  # TODO✓ FIGURE OUT SSL AND CERT SITUATION
            'verify': True,
            'timeout': 30,
        }
        self.reidrect_url = MAIB_TEST_REDIRECT_URL if IS_TEST else MAIB_LIVE_REDIRECT_URL
        self.client_ip_addr = HOST  # TODO✓ USE EVERYWHERE "✓"

    def register_sms_transaction(self, amount, currency, description='', language='ru'):
        """
        :param amount:
        :param currency:
        :param description:
        :param language:
        :return: Return URL of prepared transaction
        """
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='v',
                msg_type='SMS',
                amount=str(amount * 100),
                currency=currency,
                client_ip_addr=self.client_ip_addr,
                description=description,
                language=language
            ),
            **self.default_request_args
        )
        logger.info(f"Got response from maib {data.status_code}, {data.text}")
        return f"{self.reidrect_url}?trans_id={data.json()['transaction_id']}"

    # TODO✓: Implement other methods, same approach

    def register_dms_authorization(self, amount, currency, description='', language='ru'):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='a',
                amount=str(amount * 100),  # ?
                currency=currency,
                msg_type='DMS',
                client_ip_addr=self.client_ip_addr,
                description=description,
                language=language
            ),
            **self.default_request_args
        )

    def make_dms_trans(self, authID, amount, currency, description='', language='ru'):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='t',
                trans_id=authID,
                amount=str(amount * 100),  # ?
                currency=currency,
                client_ip_addr=self.client_ip_addr,
                msg_type='DMS',
                description=description,
                language=language
            ),
            **self.default_request_args
        )

    def get_transaction_result(self, transID):  # sa sters  , clientIpAddr din taote functiile
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='c',
                transID=transID,
                clientIpAddr=self.client_ip_addr
            ),
            **self.default_request_args
        )

    def close_day(self):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='b',
            ),
            **self.default_request_args
        )
