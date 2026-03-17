from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class PetCategory(Base):
    __tablename__ = "pet_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    name_en = Column(String(50), nullable=True)
    parent_id = Column(Integer, ForeignKey("pet_categories.id"), nullable=True)
    icon = Column(String(100), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    parent = relationship("PetCategory", remote_side=[id], backref="children")

class PetBreed(Base):
    __tablename__ = "pet_breeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    name_en = Column(String(50), nullable=False)
    category_id = Column(Integer, ForeignKey("pet_categories.id"), nullable=False)
    image = Column(LargeBinary(length=16777215), nullable=True)
    description = Column(Text, nullable=True)
    origin = Column(String(100), nullable=True)
    personality = Column(Text, nullable=True)
    care_tips = Column(Text, nullable=True)
    diet_needs = Column(Text, nullable=True)
    health_issues = Column(Text, nullable=True)
    exercise_needs = Column(String(50), nullable=True)
    size = Column(String(20), nullable=True)
    lifespan = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    category = relationship("PetCategory", backref="breeds")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    email = Column(String(100), unique=True, index=True, nullable=True)
    avatar = Column(LargeBinary(length=16777215), nullable=True)
    nickname = Column(String(50), nullable=True)
    role = Column(String(20), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 邮箱验证字段
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    verification_expire = Column(DateTime(timezone=True), nullable=True)
    
    # 关联文章
    articles = relationship("Article", back_populates="author")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    cover_image = Column(String(255), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联作者
    author = relationship("User", back_populates="articles")
