import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
from urllib.parse import quote_plus
from config import settings

# 从统一配置读取数据库连接信息，支持环境变量覆盖
DB_USER = os.getenv("DB_USER", settings.DATABASE_URL.split("://")[1].split(":")[0] if "://" in settings.DATABASE_URL else "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "abc&123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "yolo_system")

encoded_password = quote_plus(DB_PASSWORD)

SERVER_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"

def create_database_if_not_exists():
    try:
        temp_engine = create_engine(SERVER_URL)
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{DB_NAME}' checked/created successfully.")
    except Exception as e:
        print(f"Warning: Could not create database automatically: {e}")

create_database_if_not_exists()

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
