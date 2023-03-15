from enum import IntEnum
from http import HTTPStatus

from pydantic import BaseModel


class ErrorEnum(IntEnum):
    INVALID = HTTPStatus.BAD_REQUEST
    CONFLICT = HTTPStatus.CONFLICT
    UNAUTHORIZED = HTTPStatus.UNAUTHORIZED
    NOT_FOUND = HTTPStatus.NOT_FOUND


class Error(BaseModel):
    error_type: ErrorEnum
    message: str
