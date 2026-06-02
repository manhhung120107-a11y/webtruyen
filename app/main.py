from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from routers import stories, admin, sync, auth # <-- Thêm chữ 'sync' vào đây

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Web Đọc Truyện API")

# ----- THÊM ĐOẠN NÀY ĐỂ CHO PHÉP FRONTEND GỌI API -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi nguồn (sau này đưa lên mạng sẽ sửa lại cho an toàn)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)

app.include_router(stories.router)
app.include_router(admin.router)
app.include_router(sync.router) # <-- Thêm dòng này

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    return {"status": "success", "message": "Server đang chạy mượt mà."}