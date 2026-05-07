"""
用户服务层模块

【模块职责】
封装用户相关的业务逻辑，为路由层提供数据处理服务。

【设计原则】
1. 单一职责：每个方法只处理一个具体的业务逻辑
2. 服务层隔离：路由层不直接操作数据库，通过服务层统一处理
3. 异常处理：业务异常转换为 HTTP 异常抛出

【服务方法概览】
┌────────────────────────┬────────────────────────────────────┐
│         方法           │              功能                   │
├────────────────────────┼────────────────────────────────────┤
│ get_users              │ 获取用户列表（分页、搜索）          │
│ get_user_by_id         │ 根据 ID 获取用户                   │
│ create_user            │ 创建新用户                         │
│ update_user            │ 更新用户信息（管理员）             │
│ update_profile         │ 更新个人资料（用户自己）           │
│ delete_user            │ 删除用户                           │
└────────────────────────┴────────────────────────────────────┘

【数据流向】
路由层 → UserService 方法 → 数据库操作 → 返回格式化数据 → 路由响应
"""

from sqlalchemy.orm import Session
from typing import Optional, List
import models
import schemas
import auth
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException
import base64


class UserService:
    """
    用户服务类

    【设计模式】静态方法服务类
    不需要实例化，直接通过类调用静态方法

    【使用示例】
    user = UserService.get_user_by_id(db, user_id=1)
    """

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        username: Optional[str] = None
    ) -> dict:
        """
        获取用户列表

        【功能】分页查询用户列表，支持用户名模糊搜索

        【参数】
        - db: 数据库会话
        - skip: 跳过记录数（分页偏移）
        - limit: 返回记录数
        - username: 用户名过滤（模糊匹配，可选）

        【算法流程】
        1. 构建基础查询
        2. 如果有用户名过滤，添加 LIKE 条件
        3. 执行分页查询获取用户列表
        4. 统计符合条件的总记录数
        5. 格式化用户数据（处理头像等）
        6. 返回包含 items 和 total 的字典

        【返回格式】
        {
            "items": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "nickname": "管理员",
                    "role": "admin",
                    "is_verified": true,
                    "created_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-15T10:30:00"
                }
            ],
            "total": 100
        }

        【SQL 示例】
        SELECT * FROM users
        WHERE username LIKE '%keyword%'
        ORDER BY id DESC
        LIMIT 100 OFFSET 0;
        """
        # 构建查询
        query = db.query(models.User)

        # 添加用户名过滤条件
        if username:
            # 使用 LIKE 进行模糊匹配
            # % 是通配符：'%keyword%' 匹配包含 keyword 的字符串
            query = query.filter(models.User.username.like(f"%{username}%"))

        # 获取总数（在分页之前）
        total = query.count()

        # 分页查询
        # offset(skip): 跳过前 skip 条记录
        # limit(limit): 最多返回 limit 条记录
        users = query.offset(skip).limit(limit).all()

        # 格式化用户数据
        items = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }

            # 处理头像：转换为 Base64
            if user.avatar:
                user_dict["avatar"] = base64.b64encode(user.avatar).decode('utf-8')
            else:
                user_dict["avatar"] = None

            items.append(user_dict)

        return {
            "items": items,
            "total": total
        }

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[dict]:
        """
        根据 ID 获取用户

        【功能】查询指定 ID 的用户信息

        【参数】
        - db: 数据库会话
        - user_id: 用户 ID

        【返回】
        用户信息字典，如果不存在返回 None

        【算法流程】
        1. 根据 ID 查询用户
        2. 如果存在，格式化返回
        3. 如果不存在，返回 None
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            return None

        # 格式化用户数据
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }

        if user.avatar:
            user_dict["avatar"] = base64.b64encode(user.avatar).decode('utf-8')

        return user_dict

    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate) -> dict:
        """
        创建新用户

        【功能】在数据库中创建新用户记录

        【参数】
        - db: 数据库会话
        - user: 用户创建数据（包含 username, password, email 等）

        【算法流程】
        1. 检查用户名是否已存在
        2. 检查邮箱是否已存在（如果提供了邮箱）
        3. 对密码进行哈希处理
        4. 创建用户 ORM 对象
        5. 保存到数据库
        6. 返回新用户信息

        【错误情况】
        - 400: 用户名已存在
        - 400: 邮箱已被注册

        【安全处理】
        密码在存储前必须经过哈希处理，不能明文存储
        """
        # -------------------------------------------------------------------------
        # 唯一性检查
        # -------------------------------------------------------------------------
        existing_user = db.query(models.User).filter(
            models.User.username == user.username
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")

        if user.email:
            existing_email = db.query(models.User).filter(
                models.User.email == user.email
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被注册")

        # -------------------------------------------------------------------------
        # 创建用户
        # -------------------------------------------------------------------------
        # 哈希密码
        hashed_password = auth.get_password_hash(user.password)

        # 创建 ORM 对象
        db_user = models.User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password,
            role=user.role if hasattr(user, 'role') and user.role else schemas.UserRole.USER
        )

        # 保存到数据库
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # 刷新以获取自增 ID 和默认值

        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role
        }

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        user_update: schemas.UserUpdate
    ) -> dict:
        """
        更新用户信息（管理员操作）

        【功能】管理员更新任意用户的信息

        【参数】
        - db: 数据库会话
        - user_id: 要更新的用户 ID
        - user_update: 更新数据（所有字段可选）

        【算法流程】
        1. 查询用户是否存在
        2. 更新提供的字段
            - 如果是密码，需要哈希处理
            - 如果是头像，需要 Base64 解码
        3. 提交更改
        4. 返回更新后的用户信息

        【部分更新】
        只更新提供的字段，未提供的字段保持不变
        利用 Pydantic 的 Optional 字段特性实现
        """
        # 查询用户
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # -------------------------------------------------------------------------
        # 更新字段
        # -------------------------------------------------------------------------
        if user_update.email is not None:
            # 检查邮箱是否被其他用户使用
            existing = db.query(models.User).filter(
                models.User.email == user_update.email,
                models.User.id != user_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
            user.email = user_update.email

        if user_update.role is not None:
            user.role = user_update.role

        if user_update.password is not None:
            # 密码需要哈希处理
            user.password_hash = auth.get_password_hash(user_update.password)

        if user_update.nickname is not None:
            user.nickname = user_update.nickname

        if user_update.avatar is not None:
            # 头像是 Base64 编码，需要解码
            user.avatar = base64.b64decode(user_update.avatar)

        # 提交更改
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role
        }

    @staticmethod
    def update_profile(
        db: Session,
        current_user: models.User,
        profile_update: schemas.UserProfileUpdate
    ) -> dict:
        """
        更新个人资料（用户自己操作）

        【功能】用户更新自己的资料（昵称、头像）

        【参数】
        - db: 数据库会话
        - current_user: 当前登录用户（从 JWT 获取）
        - profile_update: 更新数据

        【权限限制】
        普通用户只能更新自己的 nickname 和 avatar
        不能修改用户名、密码、邮箱、角色等

        【算法流程】
        1. 更新昵称（如果提供）
        2. 更新头像（如果提供，需要 Base64 解码）
        3. 提交更改
        4. 返回更新后的资料
        """
        if profile_update.nickname is not None:
            current_user.nickname = profile_update.nickname

        if profile_update.avatar is not None:
            # 解码 Base64 头像数据
            current_user.avatar = base64.b64decode(profile_update.avatar)

        db.commit()
        db.refresh(current_user)

        # 返回更新后的数据
        result = {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "email": current_user.email
        }

        if current_user.avatar:
            result["avatar"] = base64.b64encode(current_user.avatar).decode('utf-8')

        return result

    @staticmethod
    def delete_user(db: Session, user_id: int) -> None:
        """
        删除用户

        【功能】从数据库中删除用户

        【参数】
        - db: 数据库会话
        - user_id: 要删除的用户 ID

        【算法流程】
        1. 查询用户是否存在
        2. 删除用户（级联删除相关数据）
        3. 提交更改

        【级联删除】
        由于 models.User 配置了 cascade="all, delete-orphan"
        删除用户时会自动删除该用户的所有文章等关联数据

        【错误情况】
        - 404: 用户不存在
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 删除用户
        db.delete(user)
        db.commit()
