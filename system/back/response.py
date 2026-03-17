"""
统一响应模块
提供标准化的 API 响应格式，遵循 RESTful API 设计规范
"""
from typing import Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel
from enum import Enum


class ResponseCode(str, Enum):
    """响应状态码枚举"""
    SUCCESS = "200"           # 成功
    CREATED = "201"           # 创建成功
    BAD_REQUEST = "400"       # 请求参数错误
    UNAUTHORIZED = "401"      # 未授权
    FORBIDDEN = "403"         # 权限不足
    NOT_FOUND = "404"         # 资源不存在
    SERVER_ERROR = "500"      # 服务器内部错误


class ResponseModel(BaseModel):
    """
    统一响应模型
    
    响应格式:
    {
        "code": "200",           # 状态码
        "message": "success",    # 响应消息
        "data": {...},           # 响应数据
        "timestamp": 1234567890  # 时间戳
    }
    """
    code: str = ResponseCode.SUCCESS
    message: str = "success"
    data: Optional[Any] = None
    timestamp: int = 0
    
    class Config:
        from_attributes = True


class PageResult(BaseModel):
    """分页结果模型"""
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


def success_response(data: Any = None, message: str = "success") -> dict:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
    
    Returns:
        统一格式的响应字典
    """
    import time
    return {
        "code": ResponseCode.SUCCESS,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def created_response(data: Any = None, message: str = "创建成功") -> dict:
    """
    创建成功响应（用于资源创建）
    
    Args:
        data: 响应数据
        message: 成功消息
    
    Returns:
        统一格式的响应字典
    """
    import time
    return {
        "code": ResponseCode.CREATED,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def error_response(code: str = ResponseCode.BAD_REQUEST, message: str = "请求错误", data: Any = None) -> dict:
    """
    创建错误响应
    
    Args:
        code: 错误状态码
        message: 错误消息
        data: 额外的错误数据
    
    Returns:
        统一格式的错误响应字典
    """
    import time
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def paginated_response(items: List[Any], total: int, page: int = 1, page_size: int = 10, message: str = "success") -> dict:
    """
    创建分页响应
    
    Args:
        items: 当前页数据列表
        total: 总数据条数
        page: 当前页码
        page_size: 每页条数
        message: 响应消息
    
    Returns:
        统一格式的分页响应字典
    """
    import time
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