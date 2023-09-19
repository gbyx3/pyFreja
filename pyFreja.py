# This is a python library for authentication and signing with Freja eID.
# Disclaimer: This is not an official library. It is not endorsed by Verisec AB.
# Purpose: This library is intended for learning purposes only.
# Code of conduct:
#    - String concatenation is done with the f-string method.

import requests
import settings
import json
import base64
import re
import time
import logging
import sys
import urllib.parse

session = requests.Session()
session.verify = settings.CA_cert
session.cert = (settings.user_cert, settings.user_key)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='./pyFreja.log')


def b64_encode(payload):
    """
    Base64 encodes a string.
    """
    return base64.b64encode(payload.encode("utf-8"))


def validate_email(email):
    """
    Validates an email address.
    """
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return True
    else:
        return False


def get_auth_result_request():
    payload = {}
    payload["includePrevious"] = "ALL"
    payload = b64_encode(json.dumps(payload))
    return session.post(
        f"https://{settings.url}/authentication/{settings.freja_api_version}/getResults",
        {"getAuthResultsRequest": payload})


def get_one_auth_result_request(auth_ref):
    """
    Gets the result of an authentication request.
    """
    payload = {}
    payload["authRef"] = auth_ref
    payload = b64_encode(json.dumps(payload))
    return session.post(
        f"https://{settings.url}/authentication/{settings.freja_api_version}/getOneResult",
        {"getOneAuthResultRequest": payload})


def init_auth_request(user_info_type, user_info):
    """
    Initializes an authentication request.
    """
    payload = {}
    if user_info_type == "email":
        if not validate_email(user_info):
            raise ValueError("Invalid email format.")
            return

    payload["userInfoType"] = user_info_type
    payload["userInfo"] = user_info
    payload["minRegistrationLevel"] = "EXTENDED"
    attributes = ["BASIC_USER_INFO", "DATE_OF_BIRTH", "REGISTRATION_LEVEL", "SSN", "AGE", "PHOTO", "COVID_CERTIFICATES"]
    payload["attributesToReturn"] = attributes
    payload = b64_encode(json.dumps(payload))

    return session.post(
        f"https://{settings.url}/authentication/{settings.freja_api_version}/initAuthentication",
        {"initAuthRequest": payload.decode("utf-8")})


def init_sign_request(user_info_type, 
                      user_info, 
                      data_to_sign,
                      title="Sign transaction",
                      min_registration_level="EXTENDED",
                      expiry=False):
    """
    Initializes a signing request.
    """
    payload = {}
    if user_info_type == "email":
        if not validate_email(user_info):
            raise ValueError("Invalid email format.")
            returnA
    if expiry:
        payload["expiry"] = expiry

    payload["userInfoType"] = user_info_type
    payload["userInfo"] = user_info
    payload["minRegistrationLevel"] = min_registration_level
    payload["title"] = title
    payload["dataToSignType"] = "SIMPLE_UTF8_TEXT"
    payload["dataToSign"] = {"text": data_to_sign}
    payload["signatureType"] = "SIMPLE"
    attributes = [{"attribute":"BASIC_USER_INFO"}]
    payload["attributesToReturn"] = attributes
    payload = b64_encode(json.dumps(payload))

    return session.post(
        f"https://{settings.url}/sign/{settings.freja_api_version}/initSignature",
        {"initSignRequest": payload.decode("utf-8")})


def get_qr_code(signing_ref):
    """
    Fetch the QR code
    """
    payload = f"frejaeid://bindUserToTransaction?transactionReference={signing_ref}"
    params = {"qrcodedata": urllib.parse.quote(payload)}

    return requests.get(
        "https://resources.test.frejaeid.com/qrcode/generate",
        params=params)


def generate_qr():
    auth_ref = init_auth_request("INFERRED", "N/A").json()["authRef"]
    print(auth_ref)
    signing_ref = init_sign_request("INFERRED", "N/A", auth_ref).json()
    print(signing_ref)
    qr = get_qr_code(signing_ref["signRef"])
    print(qr.url)


if __name__ == "__main__":
    generate_qr()
