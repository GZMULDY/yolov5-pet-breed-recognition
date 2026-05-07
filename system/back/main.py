"""
FastAPI 应用主入口模块

【模块职责】
负责 FastAPI 应用的初始化、中间件配置、路由注册以及启动时的数据初始化工作。

【架构说明】
本模块作为整个后端服务的入口点，采用模块化设计：
- 配置层：通过 config.py 读取环境配置
- 数据层：通过 database.py 和 models.py 管理数据库连接和 ORM 模型
- 认证层：通过 auth.py 实现 JWT 认证和密码哈希
- 路由层：通过 routers/ 目录下的模块处理具体业务逻辑
- 服务层：通过 services/ 目录下的模块封装业务逻辑

【数据流向】
HTTP 请求 → CORS 中间件 → 日志中间件 → 路由匹配 → 依赖注入（认证/数据库会话）
    → 业务逻辑处理 → 统一响应格式 → HTTP 响应
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
from pathlib import Path

# =============================================================================
# 路径配置
# =============================================================================
# 将当前目录添加到 Python 路径，确保后续导入语句能正确解析当前包内的模块
# 【原因】FastAPI 在加载模块时需要正确的包路径，否则会出现 ModuleNotFoundError
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# =============================================================================
# 内部模块导入
# =============================================================================
import models                  # ORM 模型定义，包含所有数据库表的映射类
import database                # 数据库连接配置，提供 SessionLocal 和 engine
import auth                    # 认证模块，包含 JWT 生成和密码验证函数
import schemas                 # Pydantic 模型，用于请求/响应数据的验证和序列化
from config import settings    # 配置管理，从环境变量读取配置项
from routers import auth as auth_router           # 用户认证相关 API
from routers import articles as article_router    # 文章管理相关 API
from routers import pets as pets_router           # 宠物品种管理相关 API
from routers import upload as upload_router       # 文件上传相关 API

# =============================================================================
# YOLOv5 预测路由导入（可选依赖）
# =============================================================================
# 【说明】预测模块依赖 PyTorch 和 YOLOv5，这些依赖较大且在某些部署环境下可能不需要
# 因此采用 try-except 模式进行可选导入，即使预测模块不可用，其他功能依然正常运行
try:
    from routers import predict as predict_router
    PREDICT_AVAILABLE = True
    print("Predict router imported successfully")
except ImportError as e:
    import traceback
    print(f"Warning: predict router not available due to missing dependencies: {e}")
    traceback.print_exc()
    PREDICT_AVAILABLE = False
    predict_router = None

# =============================================================================
# FastAPI 应用实例创建
# =============================================================================
# 创建 FastAPI 应用实例，这是整个 Web 服务的核心对象
# 后续的中间件、路由、事件处理器都需要注册到这个实例上
app = FastAPI()

# CORS 中间件：必须在所有中间件之后添加，确保它的响应处理包裹其他所有中间件。
# add_middleware 添加顺序决定了中间件的执行顺序（后添加的先执行），
# CORS 中间件必须是最外层（最后添加），以便给所有响应（包括错误响应）添加 CORS 头。

# =============================================================================
# 请求日志中间件
# =============================================================================
# 【作用】记录所有 HTTP 请求和响应，便于调试和问题排查
# 【执行时机】每个请求到达时，在路由处理之前和之后都会执行
# 【实现原理】使用 Starlette 的 HTTP 中间件实现请求拦截
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    HTTP 请求日志中间件

    【功能】
    1. 记录每个请求的方法和 URL
    2. 记录响应状态码
    3. 捕获并记录未处理的异常

    【参数传递链】
    request (Request) → call_next (调用下一个处理器) → response (响应对象)

    【错误处理】
    当路由处理过程中抛出异常时，将异常信息记录并返回 500 错误响应
    """
    print(f"[Request] {request.method} {request.url}")
    try:
        # 调用下一个中间件或路由处理器
        response = await call_next(request)
        print(f"[Response] {request.method} {request.url} - Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"[Error] {request.method} {request.url} - Error: {e}")
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# =============================================================================
# CORS（跨域资源共享）中间件配置
# =============================================================================
# 【重要】CORS 中间件在所有中间件之后添加（最外层），确保所有响应都有 CORS 头
# 包括错误响应（500 等），否则浏览器会因缺少 CORS 头而阻止前端读取错误信息
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 静态文件服务挂载
# =============================================================================
# 【作用】提供静态文件访问服务，如用户上传的图片、AI 检测结果图等
# 【URL 映射】/static/* → STATIC_DIR 目录下的文件
# 【自动创建】若静态文件目录不存在，则自动创建
static_dir = settings.STATIC_DIR
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# =============================================================================
# 数据库表初始化
# =============================================================================
# 【作用】根据 ORM 模型定义自动创建数据库表结构
# 【执行时机】模块加载时立即执行，确保表结构是最新版本
# 【注意】此操作不会删除已有表，只是创建不存在的新表（非迁移）
models.Base.metadata.create_all(bind=database.engine)

# =============================================================================
# 应用启动事件处理器
# =============================================================================
@app.on_event("startup")
def startup_event():
    """
    应用启动时执行的初始化逻辑

    【执行时机】FastAPI 应用启动完成、开始接收请求之前

    【初始化内容】
    1. 创建默认管理员账户（如果不存在）
    2. 创建默认测试用户（如果不存在）
    3. 初始化宠物品种数据（分类和品种信息）

    【数据库会话管理】
    使用 try-finally 确保数据库会话正确关闭，避免连接泄露

    【幂等性】
    所有初始化操作都是幂等的，多次执行不会产生重复数据
    """
    db = database.SessionLocal()
    try:
        # -------------------------------------------------------------------------
        # 创建默认管理员用户
        # -------------------------------------------------------------------------
        # 检查数据库中是否已存在 admin 用户
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            # 对默认密码进行哈希处理，使用 pbkdf2_sha256 算法
            hashed_password = auth.get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            db_user = models.User(
                username="admin",
                password_hash=hashed_password,
                role=schemas.UserRole.ADMIN    # 管理员角色，拥有所有权限
            )
            db.add(db_user)
            db.commit()
            print(f"Default admin created: admin / {settings.DEFAULT_ADMIN_PASSWORD}")

        # -------------------------------------------------------------------------
        # 创建默认普通用户（用于测试）
        # -------------------------------------------------------------------------
        test_user = db.query(models.User).filter(models.User.username == "user").first()
        if not test_user:
            hashed_password = auth.get_password_hash(settings.DEFAULT_USER_PASSWORD)
            db_user = models.User(
                username="user",
                password_hash=hashed_password,
                role=schemas.UserRole.USER    # 普通用户角色，权限受限
            )
            db.add(db_user)
            db.commit()
            print(f"Default user created: user / {settings.DEFAULT_USER_PASSWORD}")

        # -------------------------------------------------------------------------
        # 初始化宠物品种数据
        # -------------------------------------------------------------------------
        # 【数据内容】猫类/狗类的分类层级，以及各品种的详细信息
        # 【幂等性】如果数据库中已有宠物分类数据，则跳过初始化
        try:
            import init_pets
            init_pets.init_pet_data()
        except Exception as e:
            print(f"Pet data initialization: {e}")

    finally:
        # 确保数据库会话关闭，释放连接资源
        db.close()

# =============================================================================
# 路由注册
# =============================================================================
# 将各功能模块的路由注册到主应用
# 所有 API 都使用 /api/v1 作为统一前缀，遵循 RESTful 风格版本控制

# 用户认证相关 API：登录、注册、验证码、用户信息等
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])

# 文章管理相关 API：文章的 CRUD 操作
app.include_router(article_router.router, prefix="/api/v1", tags=["articles"])

# 宠物品种相关 API：品种查询、分类树、品种详情等
app.include_router(pets_router.router, prefix="/api/v1", tags=["pets"])

# 文件上传相关 API：图片上传、静态资源访问
app.include_router(upload_router.router, prefix="/api/v1", tags=["upload"])

# AI 预测相关 API：图像识别、视频检测（可选，依赖 YOLOv5）
if PREDICT_AVAILABLE:
    app.include_router(predict_router.router, prefix="/api/v1", tags=["predict"])

# =============================================================================
# 根路由
# =============================================================================
@app.get("/")
def read_root():
    """
    API 根路由 - 健康检查端点

    【用途】
    1. 确认后端服务正常运行
    2. 用于负载均衡器的健康检查
    3. 作为 API 文档的入口提示

    【返回】简单的 JSON 消息，表明服务正在运行
    """
    return {"message": "System Backend is running"}
