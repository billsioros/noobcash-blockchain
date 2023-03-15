from typing import Optional, Type, TypeVar

from core.error import Error, ErrorEnum
from pydantic import BaseModel

T = TypeVar("T", bound="Result")
A = TypeVar("A")


class Result(BaseModel):
    error: Optional[Error] = None
    payload: Optional[A] = None

    def __bool__(self) -> bool:
        return self.error is None

    @classmethod
    def ok(cls: Type[T], payload: Optional[A] = None) -> T:
        return cls(payload=payload)

    @classmethod
    def fail(cls: Type[T], error_type: ErrorEnum, message: str) -> T:
        return cls(error=Error(error_type=error_type, message=message))

    @classmethod
    def invalid(cls: Type[T], message: str) -> T:
        return cls.fail(ErrorEnum.INVALID, message)

    @classmethod
    def conflict(cls: Type[T], message: str) -> T:
        return cls.fail(ErrorEnum.CONFLICT, message)

    @classmethod
    def unauthorized(cls: Type[T], message: str) -> T:
        return cls.fail(ErrorEnum.UNAUTHORIZED, message)

    @classmethod
    def not_found(cls: Type[T], message: str) -> T:
        return cls.fail(ErrorEnum.NOT_FOUND, message)
