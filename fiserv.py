import base64
import datetime
import hashlib
import hmac
import http.client
import json
import logging
import pathlib
import urllib.parse

import iso4217
import pytz


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

    if logger.isEnabledFor(logging.DEBUG):
        response_obj = {
            'code': response.getcode(),
            'headers': {key: value for key, value in response.getheaders()},
            'body': response_body,
        }
        logger.debug(f'response = {json.dumps(response_obj)}')

    return response.getheader('Location')


def main() -> None:
    storename = '8128000020925'
    sharedsecret = 'dg;7m%D6iq'
    timezone = 'Europe/Berlin'

    now = datetime.datetime.now(pytz.timezone(timezone))
    currency_number = iso4217.Currency('MUR').number

    params = {
        'txntype': 'sale',
        'timezone': timezone,
        'txndatetime': f'{now:%Y:%m:%d-%H:%M:%S}',
        'hash_algorithm': 'HMACSHA256',
        # 'hashExtended': '',
        'storename': storename,
        'chargetotal': '13.00',
        'checkoutoption': 'combinedpage',
        'currency': str(currency_number),
        'paymentMethod': 'M',
        'responseSuccessURL': 'http://localhost:8000/',
        'responseFailURL': 'http://localhost:8000/',
        'comments': '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ',
    }

    params['hashExtended'] = calculate_hash(params, sharedsecret)

    logger.debug(f'request - {json.dumps(params)}')

    result = request(params)
    logger.info(result)


if __name__ == '__main__':
    logformat = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(format=logformat, level=logging.DEBUG)
    main()
