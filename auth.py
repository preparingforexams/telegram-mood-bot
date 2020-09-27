import json
import os
import jwt
import secrets
import uuid
from datetime import datetime, timedelta

import boto3
from dataclasses import dataclass
from typing import Dict, Optional

_REFRESH_TOKEN_HEADER = 'x-refresh-token'
_USERS_TABLE = os.getenv('USERS_TABLE')
_USERS_TG_TABLE = os.getenv('USERS_TG_TABLE')
_KEY_VALUE_TABLE = os.getenv('KEYVALUE_TABLE')

_jwt_secret: Optional[str] = None


@dataclass(init=False)
class Event:
    headers: Dict[str, str]
    query_parameters: Dict[str, str]
    path_parameters: Dict[str, str]
    body: str

    def json(self) -> dict:
        return json.loads(self.body)

    def __init__(self, headers, queryStringParameters, pathParameters, body, **kwargs):
        self.headers = headers
        self.query_parameters = queryStringParameters
        self.path_parameters = pathParameters
        self.body = body


def _create_output(body: Optional[dict] = None, status_code: int = 200) -> dict:
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {},
        "multiValueHeaders": {},
        "body": json.dumps(body)
    }


def proxy(fn):
    def _parsed(event: dict, context: dict) -> dict:
        return fn(Event(**event), context)

    return _parsed


@proxy
def handle_register(event: Event, context) -> dict:
    user_info = _create_refresh_token(_generate_user_id())
    refresh_token = user_info['refresh_token']
    token = _create_token(user_info['user_id'], None)
    token_pair = _create_token_pair(refresh_token, token)
    return _create_output(token_pair, status_code=201)


@proxy
def handle_refresh(event: Event, context) -> dict:
    refresh_token = event.headers.get(_REFRESH_TOKEN_HEADER)
    if not refresh_token:
        return _create_output(status_code=401)

    user_info = _get_user(refresh_token)
    if not user_info:
        return _create_output(status_code=401)

    expiration: datetime = user_info['expiration']
    now = datetime.utcnow()
    if expiration < now:
        return _create_output(status_code=401)

    user_id = user_info['user_id']
    token = _create_token(user_id, _get_telegram_user_id(user_id))

    if expiration < (now + timedelta(days=14)):
        # a.k.a expires in less than two weeks
        new_refresh_token = _create_refresh_token(user_id)['refresh_token']
        token_pair = _create_token_pair(new_refresh_token, token)
    else:
        token_pair = _create_token_pair(None, token)

    return _create_output(token_pair, status_code=200)


@proxy
def authorize_request(event: Event, context) -> dict:
    return _create_output(body=None, status_code=204)


def _generate_user_id() -> str:
    return uuid.uuid4().hex


def _generate_refresh_token() -> str:
    return secrets.token_hex(128)


def _create_refresh_token(user_id: str) -> dict:
    refresh_token = _generate_refresh_token()
    expiration = datetime.utcnow() + timedelta(days=365)
    dynamo = boto3.client('dynamodb')
    dynamo.put_item(
        TableName=_USERS_TABLE,
        Item={
            'refresh_token': {
                'S': refresh_token
            },
            'user_id': {
                'S': user_id
            },
            'expiration': {
                'N': str(expiration.timestamp())
            }
        }
    )
    # TODO check result
    return {
        'refresh_token': refresh_token,
        'user_id': user_id,
        'expiration': expiration
    }


def _get_user(refresh_token: str) -> Optional[dict]:
    dynamo = boto3.client('dynamodb')
    result = dynamo.get_item(
        TableName=_USERS_TABLE,
        Key={
            'refresh_token': {
                'S': refresh_token
            }
        }
    )
    item = result.get('Item')
    if not item:
        return None
    return {
        'refresh_token': refresh_token,
        'user_id': item['user_id']['S'],
        'expiration': datetime.utcfromtimestamp(float(item['expiration']['N']))
    }


def _get_telegram_user_id(user_id: str) -> Optional[str]:
    dynamo = boto3.client('dynamodb')
    result = dynamo.get_item(
        TableName=_USERS_TG_TABLE,
        Key={
            'user_id': {
                'S': user_id
            }
        }
    )
    item = result.get('Item')
    if not item:
        return None
    return item['tg_user_id']['S']


def _generate_jwt_secret() -> str:
    return secrets.token_hex(32)


def _get_jwt_secret() -> str:
    global _jwt_secret
    if _jwt_secret:
        return _jwt_secret
    dynamo = boto3.client('dynamodb')
    result = dynamo.get_item(
        TableName=_KEY_VALUE_TABLE,
        Key={
            'key': {
                'S': 'jwt_secret'
            }
        }
    )
    item = result.get('Item')
    if item:
        _jwt_secret = item['value']['S']
        return _jwt_secret

    _jwt_secret = _generate_jwt_secret()
    dynamo.put_item(
        TableName=_KEY_VALUE_TABLE,
        Item={
            'key': {
                'S': 'jwt_secret'
            },
            'value': {
                'S': _jwt_secret
            }
        }
    )
    return _jwt_secret


def _create_token(user_id: str, telegram_user_id: Optional[str]) -> str:
    payload = {
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'user_id': user_id,
        'telegram_user_id': telegram_user_id
    }
    return jwt.encode(payload, _get_jwt_secret()).decode('ascii')


def _create_token_pair(refresh_token: Optional[str], token: str) -> dict:
    result = {
        'accessToken': token
    }
    if refresh_token:
        result['refreshToken'] = refresh_token
    return result
