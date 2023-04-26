import requests

from maib_gateway.constants import MAIB_LIVE_BASE_URI, MAIB_TEST_BASE_URI, MAIB_TEST_CERT_KEY_URL


class MaibClient:
    def __init__(self):
        self.default_request_args = dict(
            cert=MAIB_TEST_CERT_KEY_URL,  # TODO FIGURE OUT SSL AND CERT SITUATION
            verify=True,
        )

    def register_sms_transaction(self, amount, currency, client_ip_addr, description='', language='ru'):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='v',
                msg_type='SMS',
                amount=str(amount * 100),
                currency=currency,
                client_ip_addr=client_ip_addr,
                description=description,
                language=language
            ),
            **self.default_request_args
        )
        # TODO: Do something with data

    # TODO: Implement other methods, same approach

    def register_dms_authorization(self, amount, currency, client_ip_addr, description='', language='ru'):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='a',
                amount=str(amount * 100),  # ?
                currency=currency,
                msg_type='DMS',
                client_ip_addr=client_ip_addr,
                description=description,
                language=language
            ),
            **self.default_request_args
        )

    def make_dms_trans(self, authID, amount, currency, client_ip_addr, description='', language='ru'):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='t',
                trans_id=authID,
                amount=str(amount * 100),  # ?
                currency=currency,
                client_ip_addr=client_ip_addr,
                msg_type='DMS',
                description=description,
                language=language
            ),
            **self.default_request_args
        )

    def get_transaction_result(self, transID, clientIpAddr):
        data = requests.post(
            url=MAIB_TEST_BASE_URI,
            params=dict(
                command='c',
                transID=transID,
                clientIpAddr=clientIpAddr
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

