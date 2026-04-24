"""
统一配置管理模块
使用 pydantic BaseSettings 从环境变量读取配置，支持 .env 文件
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/yolo_system"

    # JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 邮件服务
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.qq.com"
    MAIL_PORT: int = 465
    MAIL_SSL_TLS: bool = True
    MAIL_STARTTLS: bool = False

    # YOLOv5 模型
    MODEL_PATH: str = "runs/pets_breed_detection_large12/weights/best.pt"
    CONF_THRES: float = 0.25
    IOU_THRES: float = 0.45

    # 文件路径
    STATIC_DIR: str = str(Path(__file__).parent.parent / "static")

    # 默认用户密码
    DEFAULT_ADMIN_PASSWORD: str = "admin"
    DEFAULT_USER_PASSWORD: str = "user"

    # CORS
    CORS_ORIGINS: list = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()
