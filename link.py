import os
from typing import Dict
from urllib import parse

from proxy import proxy, Event, create_output

_ANDROID_PACKAGE_NAME = os.getenv('ANDROID_PACKAGE_NAME')
_FIREBASE_DOMAIN = os.getenv('FIREBASE_DOMAIN')
_DEEP_LINK_DOMAIN = os.getenv('DEEP_LINK_DOMAIN')


def _create_query_param(item) -> str:
    key, value = item
    return f"{key}={value}"


def _create_deep_link(query_parameters: dict) -> str:
    return f"https://{_DEEP_LINK_DOMAIN}/app?{parse.urlencode(query_parameters)}"


def _create_firebase_link(query_parameters: Dict[str, str]) -> str:
    deep_link = _create_deep_link(query_parameters)
    query_params = parse.urlencode({
        'link': deep_link,
        'apn': _ANDROID_PACKAGE_NAME,
    })
    return f"https://{_FIREBASE_DOMAIN}?{query_params}"


@proxy
def handle_link(event: Event, context):
    return create_output(status_code=307, headers={
        'Location': _create_firebase_link(event.query_parameters)
    })


@proxy
def handle_app_link(event: Event, context):
    return create_output(status_code=307, headers={
        'Location': f"https://play.google.com/store/apps/details?id={_ANDROID_PACKAGE_NAME}"
    })
