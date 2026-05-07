"""
文章服务层模块

【模块职责】
封装文章相关的业务逻辑，提供文章的 CRUD 服务。

【服务方法概览】
┌────────────────────────┬────────────────────────────────────┐
│         方法           │              功能                   │
├────────────────────────┼────────────────────────────────────┤
│ get_articles           │ 获取文章列表（分页）                │
│ get_article_by_id      │ 获取文章详情                        │
│ create_article         │ 创建文章                            │
│ update_article         │ 更新文章                            │
│ delete_article         │ 删除文章                            │
└────────────────────────┴────────────────────────────────────┘

【数据模型】
Article (文章表)
├── id: 文章ID
├── title: 标题
├── content: 正文内容
├── cover_image: 封面图片路径
├── author_id: 作者ID（外键 → users.id）
├── created_at: 创建时间
└── updated_at: 更新时间

【业务规则】
- 文章标题不能为空
- 文章内容不能为空
- 自动管理 created_at 和 updated_at 时间戳
"""

from sqlalchemy.orm import Session
import models
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException


class ArticleService:
    """
    文章服务类

    【设计模式】静态方法服务类

    【使用示例】
    articles, total = ArticleService.get_articles(db, skip=0, limit=20)
    """

    @staticmethod
    def get_articles(
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """
        获取文章列表

        【功能】分页查询文章列表，按创建时间倒序排列

        【参数】
        - db: 数据库会话
        - skip: 跳过记录数（分页偏移）
        - limit: 返回记录数

        【算法流程】
        1. 构建查询，按创建时间倒序排序
        2. 统计总数
        3. 执行分页查询
        4. 格式化每篇文章数据
        5. 返回 (文章列表, 总数)

        【排序说明】
        按创建时间倒序（最新发布的文章在前）

        【返回格式】
        (
            [
                {
                    "id": 1,
                    "title": "文章标题",
                    "content": "内容...",
                    "cover_image": "/static/xxx.jpg",
                    "author_id": 1,
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T10:00:00"
                }
            ],
            100  # 总数
        )

        【SQL 示例】
        SELECT * FROM articles
        ORDER BY created_at DESC
        LIMIT 20 OFFSET 0;
        """
        # 查询文章，按创建时间倒序
        articles = db.query(models.Article).order_by(
            models.Article.created_at.desc()
        ).offset(skip).limit(limit).all()

        # 统计总数
        total = db.query(models.Article).count()

        # 格式化数据
        return [_format_article(a) for a in articles], total

    @staticmethod
    def get_article_by_id(db: Session, article_id: int) -> dict:
        """
        获取文章详情

        【功能】查询指定文章的完整内容

        【参数】
        - db: 数据库会话
        - article_id: 文章ID

        【算法流程】
        1. 根据 ID 查询文章
        2. 如果不存在，抛出 404 异常
        3. 格式化并返回文章数据

        【错误情况】
        - 404: 文章不存在

        【返回格式】
        {
            "id": 1,
            "title": "文章标题",
            "content": "完整内容...",
            "cover_image": "/static/cover.jpg",
            "author_id": 1,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-02T15:30:00"
        }
        """
        article = db.query(models.Article).filter(
            models.Article.id == article_id
        ).first()

        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        return _format_article(article)

    @staticmethod
    def create_article(
        db: Session,
        title: str,
        content: str,
        author_id: int,
        cover_image: str = None
    ) -> dict:
        """
        创建文章

        【功能】在数据库中创建新文章记录

        【参数】
        - db: 数据库会话
        - title: 文章标题
        - content: 文章内容
        - author_id: 作者ID
        - cover_image: 封面图片路径（可选）

        【算法流程】
        1. 创建文章 ORM 对象
        2. 保存到数据库
        3. 刷新获取自动生成的 ID 和时间戳
        4. 返回新文章信息

        【自动字段】
        - id: 自增主键
        - created_at: 自动设置为当前时间
        - updated_at: 自动设置为当前时间（创建时与 created_at 相同）

        【返回格式】
        格式化后的文章字典，包含 id, title, content 等字段
        """
        # 创建文章 ORM 对象
        article = models.Article(
            title=title,
            content=content,
            cover_image=cover_image,
            author_id=author_id
        )

        # 保存到数据库
        db.add(article)
        db.commit()
        db.refresh(article)  # 刷新获取自增 ID 和默认时间戳

        return _format_article(article)

    @staticmethod
    def update_article(
        db: Session,
        article_id: int,
        title: str = None,
        content: str = None,
        cover_image: str = None
    ) -> dict:
        """
        更新文章

        【功能】修改文章的标题、内容或封面

        【参数】
        - db: 数据库会话
        - article_id: 文章ID
        - title: 新标题（可选）
        - content: 新内容（可选）
        - cover_image: 新封面路径（可选）

        【算法流程】
        1. 查询文章是否存在
        2. 更新提供的字段
        3. 提交更改
        4. 返回更新后的文章信息

        【部分更新】
        只更新提供的字段，未提供的字段保持不变
        - title=None: 不更新标题
        - content=None: 不更新内容

        【自动更新】
        updated_at 字段会在更新时自动更新为当前时间
        （由 models.Article 的 onupdate=datetime.now 配置）

        【错误情况】
        - 404: 文章不存在
        """
        # 查询文章
        article = db.query(models.Article).filter(
            models.Article.id == article_id
        ).first()

        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        # 更新提供的字段
        if title is not None:
            article.title = title

        if content is not None:
            article.content = content

        if cover_image is not None:
            article.cover_image = cover_image

        # 提交更改
        db.commit()
        db.refresh(article)  # 刷新获取更新后的 updated_at

        return _format_article(article)

    @staticmethod
    def delete_article(db: Session, article_id: int) -> None:
        """
        删除文章

        【功能】从数据库中删除文章

        【参数】
        - db: 数据库会话
        - article_id: 文章ID

        【算法流程】
        1. 查询文章是否存在
        2. 删除文章记录
        3. 提交更改

        【错误情况】
        - 404: 文章不存在

        【注意】
        删除操作不可逆
        """
        # 查询文章
        article = db.query(models.Article).filter(
            models.Article.id == article_id
        ).first()

        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        # 删除文章
        db.delete(article)
        db.commit()


# =============================================================================
# 辅助函数
# =============================================================================
def _format_article(a: models.Article) -> dict:
    """
    格式化文章数据

    【功能】将 Article ORM 对象转换为字典格式

    【参数】
    - a: Article ORM 对象

    【返回】
    文章数据字典

    【处理内容】
    - 转换 datetime 为 ISO 格式字符串
    - 提取所有关键信息字段
    """
    return {
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "cover_image": a.cover_image,
        "author_id": a.author_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }
