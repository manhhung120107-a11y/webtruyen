from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from services.google_docs import get_google_docs_service, extract_text_from_doc, parse_chapters

router = APIRouter(prefix="/api/sync", tags=["Admin - Đồng bộ Google Docs"])

@router.post("/{story_id}")
def sync_story_from_google_docs(story_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # KIỂM TRA QUYỀN ADMIN:
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới có quyền ra lệnh cào dữ liệu và đồng bộ chương truyện!"
        )
    # 1. Tìm bộ truyện trong MySQL
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story or not story.google_doc_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện hoặc truyện chưa có link Google Doc ID")

    try:
        # 2. Gọi Google API kéo text về
        service = get_google_docs_service()
        document = service.documents().get(documentId=story.google_doc_id).execute()
        full_text = extract_text_from_doc(document)
        
        # 3. Phân tách văn bản thành các chương sạch
        parsed_chapters = parse_chapters(full_text)
        
        if not parsed_chapters:
            return {"status": "warning", "message": "Không tìm thấy chương nào đúng định dạng 'Chương X'."}

        # 4. Lưu hoặc Cập nhật vào Database (Logic Upsert)
        synced_count = 0
        for chapter_data in parsed_chapters:
            existing_chapter = db.query(models.Chapter).filter(
                models.Chapter.story_id == story_id,
                models.Chapter.chapter_number == chapter_data["chapter_number"]
            ).first()

            if existing_chapter:
                existing_chapter.title = chapter_data["title"]
                existing_chapter.content = chapter_data["content"]
            else:
                new_chapter = models.Chapter(
                    story_id=story_id,
                    chapter_number=chapter_data["chapter_number"],
                    title=chapter_data["title"],
                    content=chapter_data["content"]
                )
                db.add(new_chapter)
            synced_count += 1
            
        db.commit()
        return {"status": "success", "message": f"Đã đồng bộ thành công {synced_count} chương truyện!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))