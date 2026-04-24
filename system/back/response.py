import time
from typing import Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel
from enum import Enum


class ResponseCode(str, Enum):
    SUCCESS = "200"
    CREATED = "201"
    BAD_REQUEST = "400"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    NOT_FOUND = "404"
    SERVER_ERROR = "500"


class ResponseModel(BaseModel):
    code: str = ResponseCode.SUCCESS
    message: str = "success"
    data: Optional[Any] = None
    timestamp: int = 0

    class Config:
        from_attributes = True


class PageResult(BaseModel):
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


def success_response(data: Any = None, message: str = "success") -> dict:
    return {
        "code": ResponseCode.SUCCESS,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def created_response(data: Any = None, message: str = "创建成功") -> dict:
    return {
        "code": ResponseCode.CREATED,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def error_response(code: str = ResponseCode.BAD_REQUEST, message: str = "请求错误", data: Any = None) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def paginated_response(items: List[Any], total: int, page: int = 1, page_size: int = 10, message: str = "success") -> dict:
    total_pages = (total + page_size - 1) // page_size
    return {
        "code": ResponseCode.SUCCESS,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
        "timestamp": int(time.time())
    }
