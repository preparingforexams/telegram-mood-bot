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


def _handle_poll(poll) -> Optional[dict]:
    pass


def _create_poll(chat_id=_CHAT_ID):
    data = {
        'chat_id': chat_id,
        'question': f"Heute, {_get_day()}, geht es mir",
        'options': ["Sehr gut", "Gut", "Nicht so gut", "Schlecht"],
        'is_anonymous': False
    }
    requests.post(_request_url("sendPoll"), json=data)


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
    return time.hour == 8


def handle_update(event, context):
    poll = event.get('poll')
    if poll:
        return _handle_poll(poll)
    elif _is_hammer_time():
        _create_poll()


def _invoke_lambda(lambda_name: str, args: dict):
    lamb = boto3.client('lambda')
    return lamb.invoke(
        FunctionName=lambda_name,
        InvocationType='Event',
        Payload=json.dumps(args)
    )


def _request_url(method: str):
    return f"https://api.telegram.org/bot{_bot_token}/{method}"
