from __future__ import annotations

import json
import locale
import os
import random
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, List
from zoneinfo import ZoneInfo

import boto3
import requests

_bot_token = os.getenv('TELEGRAM_TOKEN')
_CHAT_ID = "-1001433106001"
# _CHAT_ID = "133399998"

_TARGET_HOUR = int(os.getenv("TARGET_HOUR"))
_KV_TABLE_NAME = os.getenv("TABLE_NAME")
_USER_TABLE_NAME = os.getenv("USER_TABLE_NAME")
_RESULT2_TABLE_NAME = os.getenv("RESULT2_TABLE_NAME")
_GROUP_TABLE_NAME = os.getenv("GROUP_TABLE_NAME")


class DayOfWeek(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

    @staticmethod
    def today() -> DayOfWeek:
        time = _get_local_time()
        return DayOfWeek(time.weekday())


MemeKindParams = namedtuple("MemeKindParams", ["body_key", "method"])


class MemeKind(MemeKindParams, Enum):
    photo = MemeKindParams("photo", "sendPhoto")
    video = MemeKindParams("video", "sendVideo")
    animation = MemeKindParams("animation", "sendAnimation")


@dataclass
class Meme:
    file_id: str
    kind: MemeKind


_MEMES_BY_DAY = {
    DayOfWeek.Monday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAAM_YadeyBhYrgqfspOYJI2-"
                    "Q0CJBKoAAmS1MRsbNeBI8OUMldl34gMBAAMCAAN4AAMiBA",
        ),
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAANDYxdkpr0njPmQiA1jUPJPyhoz04MAAom-"
                    "MRt2lMFIay6HJVncG6kBAAMCAAN5AAMpBA",
        ),
    ],
    DayOfWeek.Tuesday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgQAAxkBAANBYxdhE8fUGGNR82Oh-IatiJM3m-gAAvkCAAKjsB1TKszbmqUkSXYpBA",
        ),
    ],
    DayOfWeek.Wednesday: [
        Meme(
            kind=MemeKind.photo,
            file_id="AgACAgIAAxkBAAM7YDZLM7l3_"
                    "SDr5gU6Uui6HQzT0h0AAk2xMRt69rhJVqsnsDCWduc3tAeeLgADAQADAgADbQADfJACAAEeBA",
        ),
    ],
    DayOfWeek.Thursday: [
        Meme(
            kind=MemeKind.animation,
            file_id="CgACAgIAAxkBAANEYzMf9xDKJ4ScYBT5JriNNV8L4aAAAiweAAIl4plJ4JCjKfT7dRUpBA",
        ),
    ],
    DayOfWeek.Friday: [
        Meme(
            kind=MemeKind.video,
            file_id="BAACAgIAAxkBAAM8YE0YG3NVgZdCH__27kNYL4DTj5MAAnsLAAIFyWhKhR8KzjuNll4eBA",
        ),
    ],
}


def _handle_poll(poll) -> Optional[dict]:
    pass


def _handle_poll_answer(poll_answer: dict) -> Optional[dict]:
    user = poll_answer['user']
    user_id = str(user['id'])
    poll_id = poll_answer['poll_id']
    if not _get_user(user_id):
        _update_user(user)
    # TODO: only do if user is unknown
    _add_to_group(user_id, _CHAT_ID)
    option_ids: List[int] = poll_answer['option_ids']
    if option_ids:
        option = option_ids[0]
        _update_result(poll_id, user_id, option)
    else:
        _delete_result(poll_id, user_id)


def _delete_result(poll_id: str, user_id: str):
    dynamodb = boto3.client('dynamodb')
    print(f"Deleting {poll_id}-{user_id}")
    response = dynamodb.delete_item(
        TableName=_RESULT2_TABLE_NAME,
        Key={
            'user_id': {
                'S': user_id
            },
            'poll_id': {
                'S': poll_id
            }
        }
    )


def _today() -> str:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return str(int(today.timestamp()))


def _update_result(poll_id, user_id, option: int):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.put_item(
        TableName=_RESULT2_TABLE_NAME,
        Item={
            'group_id': {
                'S': _CHAT_ID
            },
            'poll_id': {
                'S': poll_id
            },
            'user_id': {
                'S': user_id
            },
            'time': {
                'N': _today()
            },
            'option': {
                'N': str(option)
            }
        }
    )


def _get_user(user_id: str) -> Optional[dict]:
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=_USER_TABLE_NAME,
        Key={
            'user_id': {
                'S': user_id
            }
        }
    )
    item = response.get('Item')
    if not item:
        return None
    else:
        return {
            'id': user_id,
            'first_name': item['first_name']
        }


def _add_to_group(user_id: str, group_id: str):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.put_item(
        TableName=_GROUP_TABLE_NAME,
        Item={
            'user_id': {
                'S': user_id
            },
            'group_id': {
                'S': group_id
            }
        }
    )


def _update_user(user: dict):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.put_item(
        TableName=_USER_TABLE_NAME,
        Item={
            'user_id': {
                'S': str(user['id'])
            },
            'first_name': {
                'S': user['first_name']
            }
        }
    )


def _create_poll(chat_id=_CHAT_ID) -> str:
    data = {
        'chat_id': chat_id,
        'question': f"Heute, {_get_day()}, geht es mir",
        'options': ["🦦 Sehr gut", "🙂 Gut", "😪 Nicht so gut", "😞 Schlecht"],
        'is_anonymous': False
    }
    response = requests.post(_request_url("sendPoll"), json=data, timeout=60)
    print(f"Response code: {response.status_code}")
    message = response.json()
    print(json.dumps(message))
    return message['result']['message_id']


def _send_meme(meme: Meme, chat_id=_CHAT_ID):
    data = {
        'chat_id': chat_id,
        'disable_notification': True,
        meme.kind.body_key: meme.file_id
    }
    try:
        requests.post(_request_url(meme.kind.method), json=data, timeout=60)
    except Exception as e:
        print(f"Could not send meme: {e}")


def _get_local_time() -> datetime:
    now = datetime.now(tz=timezone.utc)
    berlin_tz = ZoneInfo("Europe/Berlin")
    return now.astimezone(berlin_tz)


def _get_day() -> str:
    locale.setlocale(locale.LC_TIME, "de_DE")
    return _get_local_time().strftime(r"%A %d.%m.%Y")


def _is_hammer_time() -> bool:
    time = _get_local_time()
    target_time = time.replace(hour=_TARGET_HOUR, minute=0, second=0, microsecond=0)
    diff: timedelta = abs(time - target_time)
    max_delta = timedelta(minutes=15)
    return diff <= max_delta


def _mini_dump(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"))


def handle_update(update, context) -> Optional[dict]:
    if 'poll_answer' in update:
        return _handle_poll_answer(update['poll_answer'])
    elif 'poll' in update:
        return _handle_poll(update['poll'])
    elif 'message' in update:
        return _handle_message(update['message'])
    else:
        dumped_update = _mini_dump(update)
        print(f"Unknown update type: {dumped_update}")


def _handle_message(message: dict):
    print(f"Received message: {_mini_dump(message)}")


def handle_poll_trigger(event, context):
    if _is_hammer_time():
        day_of_week = DayOfWeek.today()
        meme_choices = _MEMES_BY_DAY.get(day_of_week)
        if meme_choices:
            meme = random.choice(meme_choices)
            _send_meme(meme)

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
    requests.post(_request_url("stopPoll"), json=data, timeout=60)


def _get_last_poll_id() -> Optional[str]:
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=_KV_TABLE_NAME,
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
        TableName=_KV_TABLE_NAME,
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
