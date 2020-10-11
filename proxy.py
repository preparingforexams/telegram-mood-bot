import json

from dataclasses import dataclass
from typing import Dict, Union, Optional


def create_output(body: Optional[dict] = None, status_code: int = 200, headers=None) -> dict:
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": headers if headers else {},
        "multiValueHeaders": {},
        "body": json.dumps(body)
    }


@dataclass(init=False)
class Event:
    path: str
    http_method: str
    headers: Dict[str, str]
    query_parameters: Dict[str, str]
    path_parameters: Dict[str, str]
    request_context: Dict[str, Union[str, dict]]
    body: str

    def json(self) -> dict:
        return json.loads(self.body)

    def get_user_id(self) -> str:
        return self.request_context['authorizer']['principalId']

    def get_telegram_user_id(self) -> str:
        return self.request_context['authorizer']['telegram_user_id']

    def __init__(
            self,
            path,
            httpMethod,
            headers,
            queryStringParameters,
            pathParameters,
            requestContext,
            body,
            **kwargs):
        self.path = path
        self.http_method = httpMethod
        self.headers = headers
        self.query_parameters = queryStringParameters or dict()
        self.path_parameters = pathParameters
        self.request_context = requestContext
        self.body = body


def proxy(fn):
    def _parsed(event: dict, context: dict) -> dict:
        return fn(Event(**event), context)

    return _parsed
