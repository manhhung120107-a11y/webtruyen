from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text # <-- THÊM DÒNG NÀY ĐỂ CHẠY SQL THUẦN CHỐNG NGỦ
from database import engine, get_db
import models
from routers import stories, admin, sync, auth 

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Web Đọc Truyện API")

# ----- THÊM ĐOẠN NÀY ĐỂ CHO PHÉP FRONTEND GỌI API -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(stories.router)
app.include_router(admin.router)
app.include_router(sync.router) 

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    return {"status": "success", "message": "Server đang chạy mượt mà."}

# ----- CẤU HÌNH API CHỐNG NGỦ CHO AIVEN Ở ĐÂY -----
@app.get("/keep-alive")
def keep_alive(db: Session = Depends(get_db)):
    try:
        # Bắt SQL thực hiện câu lệnh siêu nhẹ "SELECT 1" để Aiven không bị ngủ đông
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database và Server đã thức giấc!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}