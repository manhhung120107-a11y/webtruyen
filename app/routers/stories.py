from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/stories", tags=["User - Đọc Truyện"])

# 1. Lấy toàn bộ danh sách truyện (Hiện ngoài trang chủ)
@router.get("/", response_model=List[schemas.StoryResponse])
def get_all_stories(db: Session = Depends(get_db)):
    return db.query(models.Story).all()

# 2. Lấy thông tin chi tiết 1 bộ truyện và danh sách các chương của nó
@router.get("/{story_id}", response_model=schemas.StoryDetailResponse)
def get_story_detail(story_id: int, db: Session = Depends(get_db)):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ truyện này")
    return story

# 3. Đọc một chương cụ thể của truyện
@router.get("/{story_id}/chapters/{chapter_number}", response_model=schemas.ChapterResponse)
def get_chapter(story_id: int, chapter_number: int, db: Session = Depends(get_db)):
    chapter = db.query(models.Chapter).filter(
        models.Chapter.story_id == story_id,
        models.Chapter.chapter_number == chapter_number
    ).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chương truyện không tồn tại")
    return chapter

# 4. Lưu vị trí chương đang đọc
@router.post("/{story_id}/history")
def save_reading_history(
    story_id: int, 
    chapter_number: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Bắt buộc phải có Token
):
    # Kiểm tra xem đã có lịch sử đọc bộ này chưa (Logic Upsert)
    history = db.query(models.ReadingHistory).filter(
        models.ReadingHistory.user_id == current_user.id,
        models.ReadingHistory.story_id == story_id
    ).first()

    if history:
        history.current_chapter_number = chapter_number
    else:
        new_history = models.ReadingHistory(
            user_id=current_user.id,
            story_id=story_id,
            current_chapter_number=chapter_number
        )
        db.add(new_history)
    
    db.commit()
    return {"status": "success"}

# 5. Lấy vị trí chương đọc gần nhất (Để tự động nhảy trang)
@router.get("/{story_id}/history")
def get_reading_history(
    story_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    history = db.query(models.ReadingHistory).filter(
        models.ReadingHistory.user_id == current_user.id,
        models.ReadingHistory.story_id == story_id
    ).first()
    
    if history:
        return {"current_chapter_number": history.current_chapter_number}
    
    # Nếu chưa từng đọc, mặc định trả về chương 1
    return {"current_chapter_number": 1}

# Schema để hứng dữ liệu gửi lên khi tạo truyện mới
class StoryCreateSchema(BaseModel):
    title: str
    author: str = ""
    description: str = ""
    genre: str = ""
    google_doc_id: str

# 6. API THÊM TRUYỆN MỚI
@router.post("/")
def create_story(story_data: StoryCreateSchema, db: Session = Depends(get_db)):
    # Tạo đối tượng truyện mới trong database
    new_story = models.Story(
        title=story_data.title,
        author=story_data.author,
        description=story_data.description,
        genre=story_data.genre,
        google_doc_id=story_data.google_doc_id
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story)
    return {"status": "success", "message": "Thêm bộ truyện mới thành công!", "story_id": new_story.id}

# 7. API XÓA TRUYỆN (Sẽ tự động xóa chương và lịch sử liên quan nếu cài Cascade, hoặc xóa thủ công)
@router.delete("/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ truyện này!")
    
    # Xóa lịch sử đọc và các chương trước để tránh lỗi ràng buộc khóa ngoại (Foreign Key)
    db.query(models.ReadingHistory).filter(models.ReadingHistory.story_id == story_id).delete()
    db.query(models.Chapter).filter(models.Chapter.story_id == story_id).delete()
    
    # Xóa bộ truyện
    db.delete(story)
    db.commit()
    return {"status": "success", "message": f"Đã xóa hoàn toàn bộ truyện '{story.title}'"}