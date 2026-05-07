"""
统一 API 响应格式模块

【模块职责】
提供标准化的 API 响应格式，确保所有接口返回数据结构一致。

【响应格式规范】
所有 API 响应都遵循以下 JSON 结构：
{
    "code": 200,           // 业务状态码
    "message": "success",  // 提示信息
    "data": {...},         // 业务数据
    "timestamp": 1680000000 // 响应时间戳
}

【设计原则】
1. 统一格式：无论成功还是失败，格式一致
2. 语义清晰：通过 code 和 message 明确表达结果
3. 便于调试：包含时间戳便于追踪请求

【状态码约定】
- 200: 成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误
"""

from typing import Any, Optional, Dict
from datetime import datetime
from enum import Enum
import time


# =============================================================================
# 响应状态码枚举
# =============================================================================
class ResponseCode(Enum):
    """
    统一响应状态码定义

    【状态码分类】
    - 2xx: 成功类
    - 4xx: 客户端错误
    - 5xx: 服务端错误

    【使用示例】
    if user not found:
        return error_response(
            code=ResponseCode.NOT_FOUND,
            message="用户不存在"
        )
    """
    # 成功类
    SUCCESS = 200           # 操作成功
    CREATED = 201           # 资源创建成功

    # 客户端错误类
    BAD_REQUEST = 400       # 请求参数错误
    UNAUTHORIZED = 401      # 未认证/未登录
    FORBIDDEN = 403         # 权限不足
    NOT_FOUND = 404         # 资源不存在
    CONFLICT = 409          # 资源冲突（如用户名已存在）

    # 服务端错误类
    INTERNAL_ERROR = 500    # 服务器内部错误


# =============================================================================
# 核心响应构建函数
# =============================================================================
def build_response(
    code: int,
    message: str,
    data: Optional[Any] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    构建统一格式的响应字典

    【参数说明】
    - code: 业务状态码（HTTP 状态码）
    - message: 提示信息，用于前端展示或调试
    - data: 业务数据，可以是任意类型（字典、列表、基本类型）
    - **extra_fields: 额外字段，会被合并到响应根级别

    【返回值】
    标准格式的响应字典:
    {
        "code": <code>,
        "message": <message>,
        "data": <data>,
        "timestamp": <当前时间戳>
    }

    【算法流程】
    1. 创建基础响应字典，包含 code、message、data、timestamp
    2. 如果有额外字段，合并到响应字典
    3. 返回构建好的字典

    【使用示例】
    >>> build_response(200, "success", {"id": 1, "name": "test"})
    {'code': 200, 'message': 'success', 'data': {'id': 1, 'name': 'test'}, 'timestamp': 1680000000}

    >>> build_response(200, "success", None, total=100, page=1)
    {'code': 200, 'message': 'success', 'data': None, 'timestamp': 1680000000, 'total': 100, 'page': 1}
    """
    response = {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())  # 当前 Unix 时间戳（秒）
    }

    # 合并额外字段到响应中
    # 例如：分页数据可能需要 total、page 等额外字段
    if extra_fields:
        response.update(extra_fields)

    return response


# =============================================================================
# 快捷响应函数
# =============================================================================
def success_response(data: Any = None, message: str = "操作成功", **extra_fields) -> Dict[str, Any]:
    """
    构建成功响应

    【适用场景】
    - GET 请求成功返回数据
    - PUT/PATCH 更新成功
    - DELETE 删除成功

    【参数说明】
    - data: 业务数据
    - message: 成功提示信息
    - **extra_fields: 额外字段（如分页信息）

    【返回】HTTP 200 响应

    【使用示例】
    # 返回用户信息
    return success_response(data={"id": 1, "username": "admin"})

    # 返回分页数据
    return success_response(
        data=users,
        total=100,
        page=1,
        page_size=10
    )
    """
    return build_response(
        code=ResponseCode.SUCCESS.value,
        message=message,
        data=data,
        **extra_fields
    )


def created_response(data: Any = None, message: str = "创建成功", **extra_fields) -> Dict[str, Any]:
    """
    构建资源创建成功响应

    【适用场景】
    - POST 请求创建资源成功
    - 用户注册成功
    - 文章发布成功

    【参数说明】
    - data: 新创建的资源数据（通常包含 id）
    - message: 成功提示信息

    【返回】HTTP 201 响应

    【使用示例】
    # 创建用户成功
    return created_response(
        data={"id": new_user.id, "username": new_user.username},
        message="用户创建成功"
    )
    """
    return build_response(
        code=ResponseCode.CREATED.value,
        message=message,
        data=data,
        **extra_fields
    )


def error_response(
    message: str = "操作失败",
    code: int = ResponseCode.BAD_REQUEST.value,
    data: Any = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    构建错误响应

    【适用场景】
    - 请求参数验证失败
    - 业务逻辑错误
    - 资源不存在

    【参数说明】
    - message: 错误提示信息，应清晰描述错误原因
    - code: 错误状态码（HTTP 状态码）
    - data: 错误详情数据（可选）

    【返回】错误状态码响应

    【使用示例】
    # 参数错误
    return error_response(message="用户名不能为空")

    # 资源不存在
    return error_response(
        message="用户不存在",
        code=ResponseCode.NOT_FOUND.value
    )

    # 权限不足
    return error_response(
        message="无权访问此资源",
        code=ResponseCode.FORBIDDEN.value
    )
    """
    return build_response(
        code=code,
        message=message,
        data=data,
        **extra_fields
    )


def paginated_response(
    data: list,
    total: int,
    page: int = 1,
    page_size: int = 10,
    message: str = "查询成功"
) -> Dict[str, Any]:
    """
    构建分页数据响应

    【适用场景】
    - 列表数据查询
    - 数据表格展示
    - 无限滚动加载

    【参数说明】
    - data: 当前页数据列表
    - total: 总记录数
    - page: 当前页码（从 1 开始）
    - page_size: 每页记录数
    - message: 提示信息

    【返回格式】
    {
        "code": 200,
        "message": "查询成功",
        "data": [...],           // 当前页数据
        "timestamp": 1680000000,
        "total": 100,            // 总记录数
        "page": 1,               // 当前页
        "page_size": 10,         // 每页数量
        "total_pages": 10        // 总页数
    }

    【算法说明】
    总页数 = ceil(总记录数 / 每页数量)

    【使用示例】
    # 查询用户列表（第2页，每页20条）
    users = db.query(User).offset(20).limit(20).all()
    total = db.query(User).count()
    return paginated_response(users, total, page=2, page_size=20)
    """
    # 计算总页数
    # 使用整数除法向上取整：(total + page_size - 1) // page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return build_response(
        code=ResponseCode.SUCCESS.value,
        message=message,
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# =============================================================================
# 响应数据格式化辅助函数
# =============================================================================
def format_datetime(dt: datetime) -> Optional[str]:
    """
    格式化日期时间为 ISO 格式字符串

    【参数】dt: datetime 对象

    【返回】ISO 格式字符串，如 "2024-01-15T10:30:00"

    【用途】
    在返回数据时将 datetime 对象转换为字符串，便于 JSON 序列化

    【示例】
    >>> format_datetime(datetime(2024, 1, 15, 10, 30, 0))
    '2024-01-15T10:30:00'
    """
    if dt is None:
        return None
    return dt.isoformat()


def format_orm_model(model, exclude_fields: list = None) -> Dict[str, Any]:
    """
    将 ORM 模型实例转换为字典

    【参数说明】
    - model: SQLAlchemy ORM 模型实例
    - exclude_fields: 要排除的字段名列表

    【返回】字典格式的模型数据

    【算法流程】
    1. 获取模型的所有列属性
    2. 过滤掉排除的字段
    3. 处理 datetime 类型字段
    4. 返回字典

    【使用场景】
    当 Pydantic 的 from_attributes 不够用时，手动转换模型

    【示例】
    user_dict = format_orm_model(user, exclude_fields=["password_hash"])
    """
    if model is None:
        return None

    exclude_fields = exclude_fields or []
    result = {}

    # 遍历模型的所有列
    for column in model.__table__.columns:
        field_name = column.name
        if field_name in exclude_fields:
            continue

        value = getattr(model, field_name)

        # 处理 datetime 类型
        if isinstance(value, datetime):
            value = format_datetime(value)

        result[field_name] = value

    return result
