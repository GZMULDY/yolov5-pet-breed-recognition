from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, auth
from response import success_response, created_response, error_response, ResponseCode, paginated_response
from typing import List

router = APIRouter()

@router.get("/articles")
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    articles = db.query(models.Article).order_by(models.Article.created_at.desc()).offset(skip).limit(limit).all()
    total = db.query(models.Article).count()
    article_list = [{
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "cover_image": a.cover_image,
        "author_id": a.author_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None
    } for a in articles]
    return paginated_response(items=article_list, total=total, page=skip//limit + 1, page_size=limit)

@router.get("/articles/{article_id}")
def read_article(article_id: int, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return success_response(
        data={
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "cover_image": article.cover_image,
            "author_id": article.author_id,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None
        }
    )

# --- 管理员接口 ---

@router.post("/articles", dependencies=[Depends(auth.get_current_admin_user)])
def create_article(article: schemas.ArticleCreate, current_user: models.User = Depends(auth.get_current_admin_user), db: Session = Depends(database.get_db)):
    db_article = models.Article(
        **article.dict(),
        author_id=current_user.id
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return created_response(
        data={
            "id": db_article.id,
            "title": db_article.title,
            "content": db_article.content,
            "cover_image": db_article.cover_image,
            "author_id": db_article.author_id,
            "created_at": db_article.created_at.isoformat() if db_article.created_at else None
        },
        message="文章创建成功"
    )

@router.put("/articles/{article_id}", dependencies=[Depends(auth.get_current_admin_user)])
def update_article(article_id: int, article_update: schemas.ArticleUpdate, db: Session = Depends(database.get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    if article_update.title is not None:
        db_article.title = article_update.title
    if article_update.content is not None:
        db_article.content = article_update.content
    if article_update.cover_image is not None:
        db_article.cover_image = article_update.cover_image
        
    db.commit()
    db.refresh(db_article)
    return success_response(
        data={
            "id": db_article.id,
            "title": db_article.title,
            "content": db_article.content,
            "cover_image": db_article.cover_image,
            "updated_at": db_article.updated_at.isoformat() if db_article.updated_at else None
        },
        message="文章更新成功"
    )

@router.delete("/articles/{article_id}", dependencies=[Depends(auth.get_current_admin_user)])
def delete_article(article_id: int, db: Session = Depends(database.get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(db_article)
    db.commit()
    return success_response(message="文章删除成功")
