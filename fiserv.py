import base64
import datetime
import json
import hashlib
import hmac
import http.client
import logging
import pathlib
import urllib.parse

import iso4217


def get_script_name() -> str:
    return pathlib.PurePath(__file__).stem


logger = logging.getLogger(get_script_name())


def hmac_sha256(key: str, msg: str) -> str:
    signing = hmac.new(key.encode(), msg.encode(), hashlib.sha256)
    return base64.b64encode(signing.digest()).decode()


def calculate_hash(params: dict, sharedsecret: str) -> str:
    sorted_params = dict(sorted(params.items()))
    stringToExtendedHash = '|'.join(sorted_params.values())
    return hmac_sha256(sharedsecret, stringToExtendedHash)


def request(params: dict) -> str:
    host = 'test.ipg-online.com'
    conn = http.client.HTTPSConnection(host, timeout=10)
    url = '/connect/gateway/processing'
    headers = {
        'Host': host,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    conn.request('POST', url, urllib.parse.urlencode(params), headers=headers)
    response = conn.getresponse()
    response_body = response.read().decode('utf-8')

    logger.debug(f'code = {response.getcode()}')
    for header_k, header_v in response.getheaders():
         logger.debug(f'{header_k} = {header_v}')
    logger.debug(f'body = {response_body}')

    return response.getheader('Location')


def main() -> None:
    storename = '8128000020925'
    sharedsecret = 'avUmYqSxMimv0tLNMEdezYBIKECZC6jsKqbI3QU4hJk'

    now = datetime.datetime.now(datetime.timezone.utc)
    currency_number = iso4217.Currency('MUR').number

    params = {
        'txntype': 'sale',
        'timezone': 'Europe/Berlin',
        'txndatetime': f'{now:%Y:%m:%d-%H:%M:%S}',
        'hash_algorithm': 'HMACSHA256',
        # 'hashExtended': '',
        'storename': storename,
        'chargetotal': '13.00',
        'checkoutoption': 'combinedpage',
        'currency': str(currency_number),
        'paymentMethod': 'M',
        'responseSuccessURL': 'https://localhost:8643/webshop/response_success.jsp',
        'responseFailURL': 'https://localhost:8643/webshop/response_failure.jsp',
    }

    params['hashExtended'] = calculate_hash(params, sharedsecret)

    logger.debug(f'request - {json.dumps(params)}')

    result = request(params)
    logger.info(result)


if __name__ == '__main__':
    logformat = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(format=logformat, level=logging.INFO)
    main()
