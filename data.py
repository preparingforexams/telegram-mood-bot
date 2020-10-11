import os

import boto3
from typing import Optional, Dict

from proxy import proxy, Event, create_output

_USERS_TABLE = os.getenv('USERS_TABLE')
_USERS_TG_TABLE = os.getenv('USERS_TG_TABLE')
_BOT_USERS_TABLE = os.getenv('BOT_USERS_TABLE')


@proxy
def handle_request(event: Event, context) -> dict:
    if event.path == "/data/me" and event.http_method == "GET":
        return get_user_info(event, context)
    else:
        print(event)
        return create_output(status_code=404)


def get_user_info(event: Event, context) -> dict:
    telegram_user_id = event.get_telegram_user_id()
    user = get_item(_BOT_USERS_TABLE, key('user_id', telegram_user_id), {"first_name": "S"})
    if not user:
        return create_output(status_code=404)
    first_name = user['first_name']
    return create_output({'firstName': first_name})


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
