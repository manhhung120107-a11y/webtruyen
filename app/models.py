from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base  # Sẽ được định nghĩa ở file cấu hình kết nối database

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ nối với bảng lịch sử đọc
    histories = relationship("ReadingHistory", back_populates="user", cascade="all, delete-orphan")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(100), default="Ẩn danh")
    description = Column(Text, nullable=True)
    genre = Column(String(255), nullable=True)
    cover_image = Column(String(255), default="default_cover.png")
    google_doc_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ nối với bảng chương và lịch sử
    chapters = relationship("Chapter", back_populates="story", cascade="all, delete-orphan")
    histories = relationship("ReadingHistory", back_populates="story", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text(length=4294967295), nullable=False)  # Tương đương LONGTEXT trong MySQL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    story = relationship("Story", back_populates="chapters")

    # Ràng buộc Unique kết hợp giữa story_id và chapter_number
    __table_args__ = (
        UniqueConstraint('story_id', 'chapter_number', name='_story_chapter_uc'),
    )


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True)
    current_chapter_number = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="histories")
    story = relationship("Story", back_populates="histories")