"""
文章管理路由模块

【模块职责】
提供文章的 CRUD 操作接口，支持文章的发布、编辑、删除和查询。

【API 端点概览】
┌────────────────────┬────────┬────────────────────────────────┐
│       端点          │  方法  │            功能                 │
├────────────────────┼────────┼────────────────────────────────┤
│ /articles          │ GET    │ 获取文章列表                    │
│ /articles/{id}     │ GET    │ 获取文章详情                    │
│ /articles          │ POST   │ 创建文章（管理员）              │
│ /articles/{id}     │ PUT    │ 更新文章（管理员）              │
│ /articles/{id}     │ DELETE │ 删除文章（管理员）              │
└────────────────────┴────────┴────────────────────────────────┘

【权限模型】
- 查看文章：所有用户可查看
- 创建/更新/删除文章：仅管理员可操作

【数据流向】
┌───────────────────────────────────────────────────────────────┐
│  客户端请求                                                    │
│      ↓                                                        │
│  JWT 认证（管理员操作）                                        │
│      ↓                                                        │
│  ArticleService 业务处理                                       │
│      ↓                                                        │
│  数据库操作                                                    │
│      ↓                                                        │
│  格式化响应 → 统一响应格式                                     │
└───────────────────────────────────────────────────────────────┘
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import database
import models
import schemas
import auth
from response import success_response, created_response
from services.article_service import ArticleService

# =============================================================================
# 路由器创建
# =============================================================================
router = APIRouter()


# =============================================================================
# 文章查询接口
# =============================================================================
@router.get("/articles")
def get_articles(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db)
):
    """
    获取文章列表

    【功能】分页查询文章列表，按创建时间倒序排列

    【参数】
    - skip: 跳过记录数（分页偏移），用于翻页
    - limit: 返回记录数，控制每页数据量

    【返回示例】
    {
        "code": 200,
        "data": {
            "items": [
                {
                    "id": 1,
                    "title": "文章标题",
                    "content": "文章内容...",
                    "cover_image": "/static/xxx.jpg",
                    "author_id": 1,
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00"
                }
            ],
            "total": 100
        }
    }

    【分页计算】
    - 第1页: skip=0, limit=20
    - 第2页: skip=20, limit=20
    - 第N页: skip=(N-1)*limit, limit=limit

    【数据流向】
    请求参数 → ArticleService.get_articles → 数据库分页查询 → 返回结果
    """
    articles, total = ArticleService.get_articles(db, skip=skip, limit=limit)

    return success_response(
        data={
            "items": articles,
            "total": total
        }
    )


@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    db: Session = Depends(database.get_db)
):
    """
    获取文章详情

    【功能】查询指定文章的完整内容

    【参数】
    - article_id: 文章ID

    【返回示例】
    {
        "code": 200,
        "data": {
            "id": 1,
            "title": "文章标题",
            "content": "完整的文章内容...",
            "cover_image": "/static/cover.jpg",
            "author_id": 1,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-02T15:30:00"
        }
    }

    【错误情况】
    - 404: 文章不存在

    【数据流向】
    article_id → ArticleService.get_article_by_id → 数据库查询 → 返回详情
    """
    article = ArticleService.get_article_by_id(db, article_id)
    return success_response(data=article)


# =============================================================================
# 文章管理接口（管理员）
# =============================================================================
@router.post("/articles")
def create_article(
    article: schemas.ArticleCreate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    创建文章（管理员）

    【功能】发布新文章

    【权限】管理员

    【请求体】
    {
        "title": "文章标题",
        "content": "文章正文内容...",
        "cover_image": "/static/covers/xxx.jpg"  // 可选
    }

    【处理流程】
    1. 验证请求者权限（管理员）
    2. 创建文章记录
    3. 设置作者为当前用户
    4. 返回新文章信息

    【数据验证】
    - title: 必填
    - content: 必填
    - cover_image: 可选，为图片路径

    【自动字段】
    - author_id: 自动设置为当前用户ID
    - created_at: 自动设置为当前时间
    - updated_at: 自动设置为当前时间
    """
    article_data = ArticleService.create_article(
        db,
        title=article.title,
        content=article.content,
        author_id=current_user.id,
        cover_image=article.cover_image
    )

    return created_response(data=article_data, message="文章发布成功")


@router.put("/articles/{article_id}")
def update_article(
    article_id: int,
    article: schemas.ArticleUpdate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    更新文章（管理员）

    【功能】修改文章内容

    【权限】管理员

    【参数】
    - article_id: 文章ID

    【请求体】
    只需包含要更新的字段：
    {
        "title": "新标题",
        "content": "新内容",
        "cover_image": "/static/new_cover.jpg"
    }

    【处理流程】
    1. 验证请求者权限（管理员）
    2. 查询文章是否存在
    3. 更新提供的字段
    4. 自动更新 updated_at 时间戳
    5. 返回更新后的文章信息

    【自动更新】
    - updated_at: 自动更新为当前时间
    """
    article_data = ArticleService.update_article(
        db,
        article_id=article_id,
        title=article.title,
        content=article.content,
        cover_image=article.cover_image
    )

    return success_response(data=article_data, message="文章更新成功")


@router.delete("/articles/{article_id}")
def delete_article(
    article_id: int,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    删除文章（管理员）

    【功能】删除指定文章

    【权限】管理员

    【参数】
    - article_id: 文章ID

    【处理流程】
    1. 验证请求者权限（管理员）
    2. 查询文章是否存在
    3. 删除文章记录
    4. 返回成功响应

    【错误情况】
    - 404: 文章不存在

    【注意】
    删除操作不可逆，建议前端提供确认对话框
    """
    ArticleService.delete_article(db, article_id)
    return success_response(message="文章删除成功")
