"""
数据库 ORM 模型定义模块

【模块职责】
定义所有数据库表的 ORM 映射类，实现面向对象的数据访问接口。

【设计原则】
1. 每个类对应一张数据库表
2. 类的属性对应表的列
3. 类的方法封装业务相关数据操作

【表结构概览】
┌─────────────────┐     ┌─────────────────┐
│  pet_categories │────→│   pet_breeds    │
│  (宠物分类)      │     │   (宠物品种)     │
│  自引用层级结构   │     │   外键关联分类   │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│     users       │────→│    articles     │
│    (用户表)      │     │    (文章表)      │
│  角色权限控制    │     │   外键关联作者   │
└─────────────────┘     └─────────────────┘

【关系说明】
- PetCategory 自引用：实现树形分类结构（猫→短毛猫→英短）
- PetBreed → PetCategory：品种属于某个分类
- Article → User：文章作者关联

【字段类型说明】
- LONGBLOB: MySQL 大二进制对象，用于存储图片等二进制数据
- Text: 长文本类型，用于存储文章内容等
- DateTime: 日期时间类型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary, Enum, Boolean
from sqlalchemy.orm import relationship
import database

# =============================================================================
# ORM 基类
# =============================================================================
# Base 是所有 ORM 模型的基类
# 它包含了 SQLAlchemy 所需的元数据（表映射信息）
Base = database.Base


# =============================================================================
# 用户表模型
# =============================================================================
class User(Base):
    """
    用户表 - 存储系统用户信息

    【表名】users

    【字段说明】
    ┌─────────────┬────────────┬────────────────────────────────┐
    │   字段名     │    类型    │              说明               │
    ├─────────────┼────────────┼────────────────────────────────┤
    │ id          │ Integer    │ 主键，自增                      │
    │ username    │ String(50) │ 用户名，唯一，用于登录           │
    │ password_hash│ String(255)│ 密码哈希值（非明文）            │
    │ email       │ String(100)│ 邮箱，唯一，用于找回密码         │
    │ nickname    │ String(50) │ 昵称，显示名称                  │
    │ avatar      │ LONGBLOB   │ 头像图片二进制数据               │
    │ role        │ Enum       │ 角色：admin/user                │
    │ created_at  │ DateTime   │ 账户创建时间                    │
    │ last_login  │ DateTime   │ 最后登录时间                    │
    │ is_verified │ Boolean    │ 是否已验证（邮箱激活）           │
    └─────────────┴────────────┴────────────────────────────────┘

    【权限模型】
    - admin: 管理员，拥有所有权限
    - user: 普通用户，权限受限（不能管理用户、不能删除他人文章等）

    【关系】
    - articles: 用户发表的文章列表（一对多）

    【安全注意】
    password_hash 存储的是经过 pbkdf2_sha256 哈希后的密码，
    永远不要存储明文密码！
    """
    __tablename__ = "users"

    # 主键：自增整数 ID
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")

    # 用户名：唯一标识登录用户，最长50字符
    # index=True 表示为此列创建索引，加速按用户名查询
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")

    # 密码哈希：存储经过 pbkdf2_sha256 算法处理后的密码
    # 原始密码 -> 哈希算法 -> 哈希字符串（存储在此）
    # 验证时：用户输入密码 -> 相同哈希算法 -> 对比结果
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")

    # 邮箱：用于找回密码、邮箱验证等功能
    # unique=True 确保邮箱唯一
    # nullable=True 表示邮箱可选，允许用户不设置邮箱
    email = Column(String(100), unique=True, nullable=True, comment="邮箱地址")

    # 昵称：用户的显示名称，可以重复
    nickname = Column(String(50), nullable=True, comment="用户昵称")

    # 头像：存储图片的二进制数据
    # LargeBinary 在 MySQL 中对应 LONGBLOB 类型，最大 4GB
    avatar = Column(LargeBinary, nullable=True, comment="头像图片")

    # 角色：控制用户权限
    # 使用 Enum 类型限制只能是 'admin' 或 'user'
    role = Column(Enum("admin", "user"), default="user", nullable=False, comment="用户角色")

    # 创建时间：账户注册时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 最后登录时间：每次登录成功后更新
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")

    # 是否已验证：标记邮箱是否已激活
    is_verified = Column(Boolean, default=False, comment="是否已验证")

    # -------------------------------------------------------------------------
    # 关系映射
    # -------------------------------------------------------------------------
    # 一对多关系：一个用户可以发表多篇文章
    # back_populates="author" 表示在 Article 模型中通过 author 属性反向引用
    # cascade="all, delete-orphan" 表示删除用户时同时删除其所有文章
    articles = relationship("Article", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self):
        """对象的字符串表示，用于调试和日志"""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


# =============================================================================
# 文章表模型
# =============================================================================
class Article(Base):
    """
    文章表 - 存储系统发布的文章

    【表名】articles

    【字段说明】
    ┌─────────────┬────────────┬────────────────────────────────┐
    │   字段名     │    类型    │              说明               │
    ├─────────────┼────────────┼────────────────────────────────┤
    │ id          │ Integer    │ 主键，自增                      │
    │ title       │ String(200)│ 文章标题                       │
    │ content     │ Text       │ 文章正文内容                    │
    │ cover_image │ String(255)│ 封面图片路径                    │
    │ author_id   │ Integer    │ 作者ID（外键）                  │
    │ created_at  │ DateTime   │ 发布时间                        │
    │ updated_at  │ DateTime   │ 最后修改时间                    │
    └─────────────┴────────────┴────────────────────────────────┘

    【关系】
    - author: 文章作者，关联到 User 表

    【权限控制】
    - 创建/更新/删除：仅管理员可操作
    - 查看：所有用户可查看
    """
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True, comment="文章ID")
    title = Column(String(200), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章内容")
    cover_image = Column(String(255), nullable=True, comment="封面图片路径")

    # 外键：作者ID，关联到 users 表的 id
    # ondelete="CASCADE" 表示删除用户时自动删除其文章
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="作者ID")

    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # -------------------------------------------------------------------------
    # 关系映射
    # -------------------------------------------------------------------------
    # 多对一关系：多篇文章属于一个作者
    # back_populates="articles" 与 User 模型的 articles 属性相互引用
    author = relationship("User", back_populates="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}', author_id={self.author_id})>"


# =============================================================================
# 宠物分类表模型
# =============================================================================
class PetCategory(Base):
    """
    宠物分类表 - 实现树形层级分类结构

    【表名】pet_categories

    【设计思想】
    采用自引用（Self-Referential）设计实现树形结构：
    ┌──────────────────────────────────────────────────────┐
    │  猫类 (id=1, parent_id=NULL)                          │
    │    ├── 短毛猫 (id=2, parent_id=1)                     │
    │    │     ├── 东方短毛猫 (id=3, parent_id=2)           │
    │    │     └── 英国短毛猫 (id=4, parent_id=2)           │
    │    └── 长毛猫 (id=5, parent_id=1)                     │
    │          ├── 波斯猫 (id=6, parent_id=5)               │
    │          └── 缅因猫 (id=7, parent_id=5)               │
    │  狗类 (id=8, parent_id=NULL)                          │
    │    └── ...                                            │
    └──────────────────────────────────────────────────────┘

    【字段说明】
    ┌─────────────┬────────────┬────────────────────────────────┐
    │   字段名     │    类型    │              说明               │
    ├─────────────┼────────────┼────────────────────────────────┤
    │ id          │ Integer    │ 主键，自增                      │
    │ name        │ String(100)│ 分类名称                       │
    │ name_en     │ String(100)│ 英文名称                       │
    │ parent_id   │ Integer    │ 父分类ID（自引用外键）          │
    │ icon        │ String(50) │ 图标（emoji或图标类名）         │
    │ sort_order  │ Integer    │ 排序号，值越小越靠前            │
    └─────────────┴────────────┴────────────────────────────────┘

    【自引用说明】
    parent_id 指向同表的 id：
    - NULL: 顶级分类（如"猫类"、"狗类"）
    - 非NULL: 子分类，parent_id 指向父分类的 id

    【关系】
    - children: 子分类列表（一对多，自引用）
    - parent: 父分类（多对一，自引用）
    - breeds: 该分类下的品种列表（一对多）
    """
    __tablename__ = "pet_categories"

    id = Column(Integer, primary_key=True, index=True, comment="分类ID")
    name = Column(String(100), nullable=False, comment="分类名称")
    name_en = Column(String(100), nullable=True, comment="英文名称")

    # 自引用外键：指向同表的 id
    # NULL 表示顶级分类
    # ondelete="CASCADE" 删除父分类时自动删除所有子分类
    parent_id = Column(Integer, ForeignKey("pet_categories.id", ondelete="CASCADE"), nullable=True, comment="父分类ID")

    icon = Column(String(50), nullable=True, comment="图标")
    sort_order = Column(Integer, default=0, comment="排序号")

    # -------------------------------------------------------------------------
    # 自引用关系映射
    # -------------------------------------------------------------------------
    # 子分类关系
    # remote_side=[id] 告诉 SQLAlchemy "子分类的 parent_id 指向当前记录的 id"
    # 没有 remote_side，SQLAlchemy 无法区分关系的方向
    children = relationship(
        "PetCategory",
        back_populates="parent",
        remote_side=[parent_id],       # 远程端（子分类）持有外键 parent_id
        cascade="all, delete-orphan"
    )

    # 父分类关系
    parent = relationship("PetCategory", back_populates="children", remote_side=[id])

    # 该分类下的品种列表
    breeds = relationship("PetBreed", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PetCategory(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"


# =============================================================================
# 宠物品种表模型
# =============================================================================
class PetBreed(Base):
    """
    宠物品种表 - 存储各品种的详细信息

    【表名】pet_breeds

    【字段说明】
    ┌──────────────┬────────────┬────────────────────────────────┐
    │    字段名     │    类型    │              说明               │
    ├──────────────┼────────────┼────────────────────────────────┤
    │ id           │ Integer    │ 主键，自增                      │
    │ name         │ String(100)│ 品种名称                       │
    │ name_en      │ String(100)│ 英文名称                       │
    │ category_id  │ Integer    │ 所属分类ID（外键）              │
    │ description  │ Text       │ 品种描述                       │
    │ origin       │ String(100)│ 原产地                         │
    │ personality  │ Text       │ 性格特点                       │
    │ care_tips    │ Text       │ 饲养建议                       │
    │ diet_needs   │ Text       │ 饮食需求                       │
    │ health_issues│ Text       │ 常见健康问题                   │
    │ exercise_needs│ Text      │ 运动需求                       │
    │ size         │ String(50) │ 体型大小                       │
    │ lifespan     │ String(50) │ 寿命范围                       │
    │ image        │ LONGBLOB   │ 品种图片                       │
    └──────────────┴────────────┴────────────────────────────────┘

    【关系】
    - category: 所属分类，关联到 PetCategory 表

    【数据流向】
    用户选择分类 → 显示该分类下品种列表 → 点击品种查看详情
    """
    __tablename__ = "pet_breeds"

    id = Column(Integer, primary_key=True, index=True, comment="品种ID")
    name = Column(String(100), nullable=False, comment="品种名称")
    name_en = Column(String(100), nullable=True, comment="英文名称")

    # 外键：所属分类
    category_id = Column(
        Integer,
        ForeignKey("pet_categories.id", ondelete="CASCADE"),
        nullable=False,
        comment="分类ID"
    )

    # 品种详细信息字段
    description = Column(Text, nullable=True, comment="品种描述")
    origin = Column(String(100), nullable=True, comment="原产地")
    personality = Column(Text, nullable=True, comment="性格特点")
    care_tips = Column(Text, nullable=True, comment="饲养建议")
    diet_needs = Column(Text, nullable=True, comment="饮食需求")
    health_issues = Column(Text, nullable=True, comment="常见健康问题")
    exercise_needs = Column(Text, nullable=True, comment="运动需求")
    size = Column(String(50), nullable=True, comment="体型大小")
    lifespan = Column(String(50), nullable=True, comment="寿命范围")

    # 品种图片：存储二进制数据
    image = Column(LargeBinary, nullable=True, comment="品种图片")

    # -------------------------------------------------------------------------
    # 关系映射
    # -------------------------------------------------------------------------
    # 多对一关系：一个品种属于一个分类
    category = relationship("PetCategory", back_populates="breeds")

    def __repr__(self):
        return f"<PetBreed(id={self.id}, name='{self.name}', category_id={self.category_id})>"
