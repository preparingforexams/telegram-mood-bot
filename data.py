import os
import re
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, Tuple, List

from proxy import proxy, Event, create_output

_USERS_TABLE = os.getenv('USERS_TABLE')
_USERS_TG_TABLE = os.getenv('USERS_TG_TABLE')
_BOT_USERS_TABLE = os.getenv('BOT_USERS_TABLE')
_RESULTS2_TABLE = os.getenv('RESULT2_TABLE_NAME')
_GROUPS_TABLE = os.getenv("GROUP_TABLE")
_MAX_DAYS = 30

# TODO get users groups from group table
_CHAT_ID = "-1001433106001"


@proxy
def handle_request(event: Event, context) -> dict:
    path = event.path
    method = event.http_method
    if path == "/data/me" and method == "GET":
        return get_me_user_info(event, context)
    elif path.startswith("/data/user/") and method == "GET":
        return get_other_user_info(event, context)
    elif path == "/data/mood":
        return get_moods(event, context)
    else:
        print(event)
        return create_output(status_code=404)


def get_other_user_info(event: Event, context) -> dict:
    pattern = re.compile(r"/data/user/([^/]+)/?")
    match = pattern.fullmatch(event.path)
    if not match:
        return create_output(status_code=400)
    return get_user_info(match.group(1))


def get_me_user_info(event: Event, context) -> dict:
    telegram_user_id = event.get_telegram_user_id()
    return get_user_info(telegram_user_id)


def get_user_info(telegram_user_id: str) -> dict:
    user = get_item(_BOT_USERS_TABLE, key('user_id', telegram_user_id), {"first_name": "S"})
    if not user:
        return create_output(status_code=404)
    first_name = user['first_name']
    return create_output({'firstName': first_name})


def get_moods(event: Event, context) -> dict:
    from_param = event.query_parameters.get('from')
    until_param = event.query_parameters.get('until')
    try:
        from_date, until_date = _normalize_params(from_param, until_param)
    except ValueError:
        return create_output(status_code=400)

    moods = _load_moods(from_date, until_date)

    return create_output({
        'from': int(from_date.timestamp()),
        'until': int(until_date.timestamp()),
        'moods': moods,
    })


def _load_moods(from_date: datetime, until_date: datetime) -> List[dict]:
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(_RESULTS2_TABLE)

    from_str = int(from_date.timestamp())
    until_str = int(until_date.timestamp())
    response = table.query(
        IndexName="grouped",
        KeyConditionExpression=Key('group_id').eq(_CHAT_ID) & Key('time').between(from_str, until_str),
    )
    items = response['Items']
    result = []
    current_item = None
    for item in items:
        day = int(item['time'])
        if not current_item or current_item['day'] != day:
            current_item = {
                'day': day,
                'votes': [],
            }
            result.append(current_item)
        current_item['votes'].append({
            'userId': item['user_id'],
            'option': int(item['option'])
        })
    return result


def _normalize_params(from_param: Optional[str], until_param: Optional[str]) -> Tuple[datetime, datetime]:
    if from_param:
        from_date = datetime.utcfromtimestamp(int(from_param))
    else:
        from_date = None
    if until_param:
        until_date = datetime.utcfromtimestamp(int(until_param))
    else:
        until_date = None

    max_duration = timedelta(days=_MAX_DAYS)

    if from_date and until_date:
        if until_date < from_date:
            raise ValueError("Until before from")
        if (until_date - from_date) > max_duration:
            until_date = from_date + max_duration
    elif from_date and not until_date:
        until_date = from_date + max_duration
    elif not from_date and until_date:
        from_date = until_date - max_duration
    else:
        until_date = datetime.utcnow()
        from_date = until_date - max_duration

    from_date = _to_midnight(from_date)
    until_date = _to_midnight(until_date)
    return from_date, until_date


def _to_midnight(date: datetime) -> datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def key(name: str, value: str, key_type: str = "S") -> dict:
    return {
        name: {
            key_type: value
        }
    }


def get_item(
        table_name: str,
        item_key: Dict[str, Dict[str, str]],
        content: Optional[Dict[str, str]] = None
) -> Optional[dict]:
    dynamo = boto3.client('dynamodb')
    result = dynamo.get_item(
        TableName=table_name,
        Key=item_key
    )
    item = result.get('Item')
    if not item:
        return None
    if content:
        result = dict()
        for content_key, content_type in content.items():
            result[content_key] = item[content_key][content_type]
        return result
    else:
        return item
