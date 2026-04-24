from sqlalchemy.orm import Session
import models
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException


class ArticleService:
    @staticmethod
    def get_articles(db: Session, skip: int = 0, limit: int = 20):
        articles = db.query(models.Article).offset(skip).limit(limit).all()
        total = db.query(models.Article).count()
        return [_format_article(a) for a in articles], total

    @staticmethod
    def get_article_by_id(db: Session, article_id: int):
        article = db.query(models.Article).filter(models.Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        return _format_article(article)

    @staticmethod
    def create_article(db: Session, title: str, content: str, author_id: int, cover_image: str = None):
        article = models.Article(
            title=title,
            content=content,
            cover_image=cover_image,
            author_id=author_id
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        return _format_article(article)

    @staticmethod
    def update_article(db: Session, article_id: int, title: str = None, content: str = None, cover_image: str = None):
        article = db.query(models.Article).filter(models.Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
        if cover_image is not None:
            article.cover_image = cover_image
        db.commit()
        db.refresh(article)
        return _format_article(article)

    @staticmethod
    def delete_article(db: Session, article_id: int):
        article = db.query(models.Article).filter(models.Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        db.delete(article)
        db.commit()


def _format_article(a: models.Article) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "cover_image": a.cover_image,
        "author_id": a.author_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }
