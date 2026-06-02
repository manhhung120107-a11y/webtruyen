from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin - Quản Lý Tủ Truyện"])

# 1. Tạo một bộ truyện mới
@router.post("/stories", response_model=schemas.StoryResponse)
def create_story(story: schemas.StoryCreate, db: Session = Depends(get_db)):
    db_story = models.Story(**story.model_dump())
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

# 2. Thêm một chương mới vào truyện (Hoặc cập nhật nếu đã trùng số chương - Logic Upsert)
@router.post("/stories/{story_id}/chapters", response_model=schemas.ChapterResponse)
def add_or_update_chapter(story_id: int, chapter: schemas.ChapterCreate, db: Session = Depends(get_db)):
    # Kiểm tra truyện có tồn tại không
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")

    # Kiểm tra xem chương này đã có chưa
    existing_chapter = db.query(models.Chapter).filter(
        models.Chapter.story_id == story_id,
        models.Chapter.chapter_number == chapter.chapter_number
    ).first()

    if existing_chapter:
        # Nếu đã có thì cập nhật đè nội dung chữ (Gọt sạch font từ web gửi lên)
        existing_chapter.title = chapter.title
        existing_chapter.content = chapter.content
        db.commit()
        db.refresh(existing_chapter)
        return existing_chapter
    else:
        # Nếu chưa có thì thêm mới hoàn toàn
        db_chapter = models.Chapter(**chapter.model_dump(), story_id=story_id)
        db.add(db_chapter)
        db.commit()
        db.refresh(db_chapter)
        return db_chapter

# 3. Xóa một bộ truyện (Sẽ tự động xóa sạch các chương liên quan nhờ ON DELETE CASCADE)
@router.delete("/stories/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện để xóa")
    db.delete(story)
    db.commit()
    return {"status": "success", "message": f"Đã xóa thành công truyện: {story.title}"}