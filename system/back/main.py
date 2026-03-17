from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
from pathlib import Path

# 添加当前目录到 Python 路径，确保能正确导入模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 使用明确的导入，避免模块冲突
import models
import database  
import auth
import schemas
from routers import auth as auth_router
from routers import articles as article_router
from routers import pets as pets_router
from routers import upload as upload_router
# 注意：predict 路由将在后面动态导入或在 try-except 块中处理，
# 因为它依赖于 YOLOv5 环境，如果环境未配置好可能会报错
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    print(f"[Request] {request.method} {request.url}")
    try:
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

# 挂载静态文件目录，用于访问上传的图片和识别结果
# 获取 system 目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
system_dir = os.path.dirname(current_dir)
static_dir = os.path.join(system_dir, "static")
os.makedirs(static_dir, exist_ok=True) # 确保目录存在

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    try:
        # Create default admin user if not exists
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            hashed_password = auth.get_password_hash("admin")
            db_user = models.User(
                username="admin", 
                password_hash=hashed_password,
                role=schemas.UserRole.ADMIN
            )
            db.add(db_user)
            db.commit()
            print("Default admin created: admin / admin")
        
        # Create default normal user for testing
        test_user = db.query(models.User).filter(models.User.username == "user").first()
        if not test_user:
            hashed_password = auth.get_password_hash("user")
            db_user = models.User(
                username="user", 
                password_hash=hashed_password, 
                role=schemas.UserRole.USER
            )
            db.add(db_user)
            db.commit()
            print("Default user created: user / user")

        # Initialize pet data
        try:
            import init_pets
            init_pets.init_pet_data()
        except Exception as e:
            print(f"Pet data initialization: {e}")

    finally:
        db.close()

app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(article_router.router, prefix="/api/v1", tags=["articles"])
app.include_router(pets_router.router, prefix="/api/v1", tags=["pets"])
app.include_router(upload_router.router, prefix="/api/v1", tags=["upload"])
if PREDICT_AVAILABLE:
    app.include_router(predict_router.router, prefix="/api/v1", tags=["predict"])

@app.get("/")
def read_root():
    return {"message": "System Backend is running"}
