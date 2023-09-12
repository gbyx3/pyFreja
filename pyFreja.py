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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='./pyFreja.log')


def make_request(url, payload, method="POST"):
    return requests.request(method, url, data=payload, verify=settings.CA_cert, cert=(settings.user_cert, settings.user_key))


def get_one_auth_result_request(auth_ref):
    payload = {}
    payload["authRef"] = auth_ref
    payload = b64_encode(json.dumps(payload))
    return make_request(
        f"https://{settings.url}/authentication/{settings.freja_api_version}/getOneResult",
        {"getOneAuthResultRequest": payload})


def init_auth_request(user_info_type, user_info):
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

    return make_request(
        f"https://{settings.url}/authentication/{settings.freja_api_version}/initAuthentication",
        {"initAuthRequest": payload.decode("utf-8")})


def b64_encode(payload):
    return base64.b64encode(payload.encode("utf-8"))


def validate_email(email):
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return True
    else:
        return False

if __name__ == "__main__":
    import argparse
    args = sys.argv
    if len(args) != 2:
        print("Usage: python3 pyFreja.py")
        sys.exit(1)
    email = args[1]
    auth = init_auth_request("EMAIL", email).json()
    try:
        authRef = auth["authRef"]
    except KeyError:
        print(f"Error: {auth['code']} - {auth['message']}")
        sys.exit(2)
    except Exception as e:
        print(f"Unknown Error: {e}")
        sys.exit(1)


    authResult = get_one_auth_result_request(authRef).json()
    while authResult["status"] == "STARTED":
        authResult = get_one_auth_result_request(authRef).json()
        time.sleep(1)
    while authResult["status"] == "DELIVERED_TO_MOBILE":
        authResult = get_one_auth_result_request(authRef).json()
        time.sleep(1)
    print(json.dumps(authResult, indent=4, sort_keys=True))


