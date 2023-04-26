import os

from ecommerce.settings import CERT_DIR

MAIB_LIVE_REDIRECT_URL = 'https://maib.ecommerce.md:443/ecomm01/ClientHandler'

MAIB_LIVE_BASE_URI = 'https://maib.ecommerce.md:11440/ecomm01/MerchantHandler'

MAIB_TEST_REDIRECT_URL = 'https://maib.ecommerce.md:21443/ecomm/ClientHandler'

MAIB_TEST_BASE_URI = 'https://maib.ecommerce.md:21440/ecomm/MerchantHandler'

MAIB_TEST_CERT_URL = os.path.join(CERT_DIR, 'cert.pem')

MAIB_TEST_CERT_KEY_URL = os.path.join(CERT_DIR, 'key.pem')

MAIB_TEST_CERT_PASS = 'Za86DuC$'
