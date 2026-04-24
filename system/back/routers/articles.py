from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, database, auth
from response import success_response, created_response, error_response, ResponseCode, paginated_response
from services.article_service import ArticleService

router = APIRouter()

@router.get("/articles")
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    articles, total = ArticleService.get_articles(db, skip=skip, limit=limit)
    return paginated_response(items=articles, total=total, page=skip//limit + 1, page_size=limit)

@router.get("/articles/{article_id}")
def read_article(article_id: int, db: Session = Depends(database.get_db)):
    return success_response(data=ArticleService.get_article_by_id(db, article_id))

@router.post("/articles")
def create_article(article: schemas.ArticleCreate, current_user: models.User = Depends(auth.get_current_admin_user), db: Session = Depends(database.get_db)):
    data = ArticleService.create_article(db, article.title, article.content, current_user.id, article.cover_image)
    return created_response(data=data, message="文章创建成功")

@router.put("/articles/{article_id}")
def update_article(article_id: int, article_update: schemas.ArticleUpdate, current_user: models.User = Depends(auth.get_current_admin_user), db: Session = Depends(database.get_db)):
    data = ArticleService.update_article(db, article_id, article_update.title, article_update.content, article_update.cover_image)
    return success_response(data=data, message="文章更新成功")

@router.delete("/articles/{article_id}")
def delete_article(article_id: int, current_user: models.User = Depends(auth.get_current_admin_user), db: Session = Depends(database.get_db)):
    ArticleService.delete_article(db, article_id)
    return success_response(message="文章删除成功")
