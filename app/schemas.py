from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Schema hứng dữ liệu đăng ký tài khoản mới
class UserRegister(BaseModel):
    username: str
    password: str

# --- SCHEMAS CHO CHƯƠNG (CHAPTER) ---
class ChapterBase(BaseModel):
    chapter_number: int
    title: Optional[str] = None
    content: str

class ChapterCreate(ChapterBase):
    pass

class ChapterResponse(ChapterBase):
    id: int
    story_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- SCHEMAS CHO TRUYỆN (STORY) ---
class StoryBase(BaseModel):
    title: str
    author: Optional[str] = "Ẩn danh"
    description: Optional[str] = None
    cover_image: Optional[str] = "default_cover.png"
    google_doc_id: Optional[str] = None

class StoryCreate(StoryBase):
    pass

class StoryResponse(StoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schema hiển thị chi tiết truyện kèm danh sách chương (dùng cho trang mục lục)
class StoryDetailResponse(StoryResponse):
    chapters: List[ChapterResponse] = []