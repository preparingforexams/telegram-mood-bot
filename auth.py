import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import boto3
import jwt
from jwt import InvalidTokenError

from proxy import proxy, Event, create_output

_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
_REFRESH_TOKEN_HEADER = 'x-refresh-token'
_USERS_TABLE = os.getenv('USERS_TABLE')
_USERS_TG_TABLE = os.getenv('USERS_TG_TABLE')
_KEY_VALUE_TABLE = os.getenv('KEYVALUE_TABLE')
_API_RESOURCE = os.getenv('API_RESOURCE')

_jwt_secret: Optional[str] = None


@proxy
def handle_register(event: Event, context) -> dict:
    user_info = _create_refresh_token(_generate_user_id())
    refresh_token = user_info['refresh_token']
    token = _create_token(user_info['user_id'], None)
    token_pair = _create_token_pair(refresh_token, token)
    return create_output(token_pair, status_code=201)


@proxy
def handle_refresh(event: Event, context) -> dict:
    refresh_token = event.headers.get(_REFRESH_TOKEN_HEADER)
    if not refresh_token:
        return create_output(status_code=401)

    user_info = _get_user(refresh_token)
    if not user_info:
        return create_output(status_code=401)

    expiration: datetime = user_info['expiration']
    now = datetime.utcnow()
    if expiration < now:
        return create_output(status_code=401)

    user_id = user_info['user_id']
    token = _create_token(user_id, _get_telegram_user_id(user_id))

    if expiration < (now + timedelta(days=14)):
        # a.k.a expires in less than two weeks
        new_refresh_token = _create_refresh_token(user_id)['refresh_token']
        token_pair = _create_token_pair(new_refresh_token, token)
    else:
        token_pair = _create_token_pair(None, token)

    return create_output(token_pair, status_code=200)


@proxy
def handle_telegram_id(event: Event, context) -> dict:
    body = event.json()
    # id, first_name, last_name, username, photo_url, auth_date, hash
    telegram_user_id = _validate_telegram_data(body)
    if not telegram_user_id:
        return create_output(status_code=403)

    user_id = event.get_user_id()
    _put_telegram_user_id(user_id, telegram_user_id)

    token = _create_token(user_id, telegram_user_id)
    token_pair = _create_token_pair(None, token)
    return create_output(token_pair)


def _validate_telegram_data(data: dict) -> Optional[str]:
    expected_hash = data.pop('hash')
    if not expected_hash:
        print("Missing hash")
        return

    check_string = "\n".join(map(lambda x: f"{x[0]}={x[1]}", sorted(data.items())))
    secret_key = hashlib.sha256(_BOT_TOKEN.encode('utf-8')).digest()
    actual_hash = hmac.digest(secret_key, check_string.encode('utf-8'), hashlib.sha256).hex()
    if expected_hash != actual_hash:
        print("Hash mismatch")
        return

    yesterday = datetime.utcnow() - timedelta(days=1)
    auth_date = datetime.utcfromtimestamp(int(data['auth_date']))
    if auth_date < yesterday:
        print("Outdated auth data")
        return

    return data['id']


def authorize_request(event: dict, context) -> dict:
    token: str = event['authorizationToken']
    prefix_length = len("Bearer ")
    if token and len(token) > prefix_length:
        token_content = token[prefix_length:]
    else:
        print("Token missing or too short")
        return _build_authorizer_response("user", None, {})
    try:
        payload = jwt.decode(token_content, _get_jwt_secret())
    except InvalidTokenError as e:
        print(e)
        print("Invalid token")
        return _build_authorizer_response("user", None, {})

    telegram_user_id = payload.get('telegram_user_id')
    context = _build_context(telegram_user_id)
    allowed_path = "*" if telegram_user_id else "auth"
    return _build_authorizer_response(payload['user_id'], allowed_path, context)


def _build_authorizer_response(principal_id: str, allowed: Optional[str], context: dict) -> dict:
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': "2012-10-17",
            'Statement': [
                {
                    'Action': "execute-api:Invoke",
                    'Effect': "Allow" if allowed else "Deny",
                    'Resource': _API_RESOURCE + (allowed if allowed else "*")
                }
            ]
        },
        'context': context
    }


def _build_context(telegram_user_id: Optional[str]) -> dict:
    if telegram_user_id:
        return {
            'telegram_user_id': telegram_user_id
        }
    else:
        return {}


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


def _put_telegram_user_id(user_id: str, telegram_user_id: str):
    dynamo = boto3.client('dynamodb')
    dynamo.put_item(
        TableName=_USERS_TG_TABLE,
        Item={
            'user_id': {
                'S': user_id
            },
            'tg_user_id': {
                'S': telegram_user_id
            }
        }
    )


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
