import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
from urllib.parse import quote_plus

# 默认配置，支持环境变量覆盖
DB_USER = os.getenv("DB_USER", "root")
# 这里设置为您提供的默认密码
DB_PASSWORD = os.getenv("DB_PASSWORD", "abc&123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "yolo_system")

# 对密码进行 URL 编码，防止特殊字符（如 @, :, & 等）导致解析错误
encoded_password = quote_plus(DB_PASSWORD)

# 1. 首先尝试连接到 MySQL Server (不指定数据库)，用于创建数据库
SERVER_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"

def create_database_if_not_exists():
    try:
        # 创建临时引擎连接到 Server
        temp_engine = create_engine(SERVER_URL)
        with temp_engine.connect() as conn:
            # 提交事务（CREATE DATABASE 不能在事务块中运行，需要自动提交模式）
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{DB_NAME}' checked/created successfully.")
    except Exception as e:
        print(f"Warning: Could not create database automatically: {e}")

# 尝试自动创建数据库
create_database_if_not_exists()

# 2. 连接到具体数据库
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建数据库引擎
# check_same_thread 是 SQLite 特有的，MySQL 不需要
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 自动重连
    pool_recycle=3600    # 连接回收时间
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
