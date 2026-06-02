import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import bcrypt
import jwt
import models
from database import get_db
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = "HS256"

router = APIRouter(prefix="/api/auth", tags=["User - Xác thực tài khoản"])

# --- SCHEMAS CHO ĐĂNG NHẬP ---
class AuthSchema(BaseModel):
    username: str
    password: str

# --- 1. API ĐĂNG KÝ TÀI KHOẢN ---
@router.post("/register")
def register(user_data: AuthSchema, db: Session = Depends(get_db)):
    # Kiểm tra xem tài khoản đã tồn tại chưa
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Tài khoản này đã tồn tại!")

    # Mã hóa mật khẩu bằng bcrypt trước khi lưu vào MySQL
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = models.User(username=user_data.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    
    return {"status": "success", "message": "Đăng ký tài khoản thành công!"}

# --- 2. API ĐĂNG NHẬP (CẤP TOKEN) ---
@router.post("/login")
def login(user_data: AuthSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Tài khoản hoặc mật khẩu không chính xác")

    # Kiểm tra mật khẩu nhập vào với mật khẩu đã mã hóa trong DB
    if not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Tài khoản hoặc mật khẩu không chính xác")

    # Tạo JWT Token có thời hạn 7 ngày để giữ phiên đăng nhập
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "exp": expiration
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Giải mã token để lấy username
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn hoặc không hợp lệ")
    
    # Tìm user trong MySQL
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Không tìm thấy người dùng")
    
    return user