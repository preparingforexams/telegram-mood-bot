import json
import locale
import os
from datetime import datetime
from typing import Optional

import boto3
import pytz
import requests

_bot_token = os.getenv('TELEGRAM_TOKEN')
_CHAT_ID = "-1001433106001"
# _CHAT_ID = "133399998"
_TARGET_HOUR = int(os.getenv("TARGET_HOUR"))
_TABLE_NAME = os.getenv("TABLE_NAME")


def _handle_poll(poll) -> Optional[dict]:
    pass


def _create_poll(chat_id=_CHAT_ID) -> str:
    data = {
        'chat_id': chat_id,
        'question': f"Heute, {_get_day()}, geht es mir",
        'options': ["Sehr gut", "Gut", "Nicht so gut", "Schlecht"],
        'is_anonymous': False
    }
    response = requests.post(_request_url("sendPoll"), json=data)
    print(f"Response code: {response.status_code}")
    message = response.json()
    print(json.dumps(message))
    return message['result']['message_id']


def _get_local_time() -> datetime:
    now = datetime.now()
    berlin_tz = pytz.timezone("Europe/Berlin")
    return berlin_tz.fromutc(now)


def _get_day() -> str:
    locale.setlocale(locale.LC_TIME, "de_DE")
    return _get_local_time().strftime(r"%A %d.%m.%Y")


def _is_hammer_time() -> bool:
    time = _get_local_time()
    print(f"The hour is: {time.hour}")
    return time.hour == _TARGET_HOUR


def handle_update(update, context):
    return _handle_poll(update['poll'])


def handle_poll_trigger(event, context):
    if _is_hammer_time():
        poll_id = _create_poll()
        _set_last_poll_id(poll_id)


def handle_close_trigger(event, context):
    last_poll_id = _get_last_poll_id()
    if last_poll_id:
        _close_poll(last_poll_id)


def _close_poll(message_id: str):
    data = {
        "message_id": message_id,
        "chat_id": _CHAT_ID
    }
    requests.post(_request_url("stopPoll"), json=data)


def _get_last_poll_id() -> Optional[str]:
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=_TABLE_NAME,
        Key={
            'key': {
                'S': 'last_poll_id'
            }
        }
    )
    print(json.dumps(response))
    poll_id = response['Item']['value']['S']
    return poll_id


def _set_last_poll_id(poll_id):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.put_item(
        TableName=_TABLE_NAME,
        Item={
            'key': {
                'S': 'last_poll_id'
            },
            'value': {
                'S': str(poll_id)
            }
        }
    )
    print(json.dumps(response))


def _request_url(method: str):
    return f"https://api.telegram.org/bot{_bot_token}/{method}"
