"""
数据库连接与会话管理模块

【模块职责】
管理 SQLAlchemy 数据库引擎和会话，提供数据库连接的创建、获取和释放机制。

【核心组件】
1. create_engine: 创建数据库引擎，管理连接池
2. SessionLocal: 会话工厂，用于创建数据库会话
3. get_db: 依赖注入函数，为每个请求提供独立的数据库会话

【连接池机制】
SQLAlchemy 使用连接池来管理数据库连接：
- 预创建一定数量的连接，避免频繁创建/销毁连接的开销
- 连接复用，提高性能
- 自动处理连接泄漏和超时

【会话生命周期】
请求开始 → get_db() 创建会话 → 业务操作 → 请求结束 → 会话自动关闭

【注意事项】
1. 使用 yield 语法确保会话正确关闭
2. 不要在模块级别创建会话后长期持有
3. 生产环境应配置连接池参数优化性能
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

# =============================================================================
# 数据库引擎创建
# =============================================================================
# 【create_engine 参数说明】
#
# 第一个参数 - 数据库连接 URL:
#   格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
#   - mysql: 数据库类型
#   - +pymysql: 使用 PyMySQL 作为 MySQL 驱动（纯 Python 实现，兼容性好）
#   - 用户名、密码: 数据库认证信息
#   - 主机:端口: 数据库服务器地址
#   - 数据库名: 要使用的数据库
#
# pool_pre_ping=True:
#   每次使用连接前检查连接是否有效
#   【作用】自动检测并处理数据库连接断开的情况
#   【场景】适用于长时间运行的服务，防止"MySQL has gone away"错误
#
# pool_recycle=3600:
#   连接回收时间（秒）
#   【作用】超过这个时间的连接会被自动回收重建
#   【原因】MySQL 默认 wait_timeout=28800 秒（8小时）后会关闭不活跃连接
#          设置小于 28800 可避免"连接已关闭"错误
#
# echo=False:
#   是否打印 SQL 语句到控制台
#   【调试】开发时设为 True 可查看执行的 SQL；生产环境设为 False
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600,     # 每小时回收连接
    echo=False             # 不打印 SQL 语句
)

# =============================================================================
# 会话工厂配置
# =============================================================================
# 【SessionLocal 说明】
# 这是一个工厂类，用于创建数据库会话实例
# 每次调用 SessionLocal() 都会创建一个新的会话
#
# 【参数说明】
# autocommit=False:
#   不自动提交事务
#   【原因】需要手动控制事务提交，保证数据一致性
#   【用法】修改数据后需要调用 db.commit() 才会持久化
#
# autoflush=False:
#   不自动刷新会话
#   【原因】自动 flush 可能在查询时意外执行未提交的修改
#   【优点】更精确地控制何时将变更同步到数据库
#
# bind=engine:
#   绑定到之前创建的数据库引擎
#   会话执行 SQL 时通过引擎获取连接
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# =============================================================================
# ORM 模型基类
# =============================================================================
# 【Base 类说明】
# 所有 ORM 模型类的基类
# SQLAlchemy 通过这个基类来发现和管理所有模型类
#
# 【使用方式】
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     ...
#
# 【元数据】
# Base.metadata 包含所有模型类的元信息（表名、列、约束等）
# 可通过 Base.metadata.create_all() 创建所有表
Base = declarative_base()


# =============================================================================
# 数据库会话依赖注入
# =============================================================================
def get_db():
    """
    FastAPI 依赖注入函数 - 获取数据库会话

    【设计模式】依赖注入（Dependency Injection）

    【工作原理】
    1. FastAPI 在处理请求前调用此函数
    2. yield 前的代码在请求前执行
    3. yield 返回会话给路由处理函数
    4. 请求处理完成后，yield 后的代码执行（清理资源）

    【生命周期】
    ```
    请求开始
        ↓
    db = SessionLocal()  # 创建会话
        ↓
    yield db              # 将会话注入到路由
        ↓
    路由处理函数执行      # 业务逻辑使用 db
        ↓
    db.close()           # 关闭会话（无论成功或异常）
        ↓
    请求结束
    ```

    【使用示例】
    @router.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()

    【异常安全】
    如果路由处理中抛出异常，finally 块仍会执行，
    确保数据库会话被正确关闭，避免连接泄漏。

    【连接池影响】
    db.close() 并非关闭数据库连接，而是将会话归还给连接池
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # 确保会话始终被关闭
        # 无论路由处理成功还是抛出异常
        db.close()
