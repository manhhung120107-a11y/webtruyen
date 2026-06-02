import os
import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Đường dẫn trỏ ra file credentials.json nằm ở thư mục backend/
CREDENTIALS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../credentials.json"))
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def get_google_docs_service():
    """Hàm khởi tạo kết nối với Google Docs bằng Service Account"""
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(f"Không tìm thấy file {CREDENTIALS_PATH}")
    
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
    return service

def extract_text_from_doc(document):
    """Hàm bóc tách chữ từ cấu trúc JSON phức tạp của Google Docs"""
    text = ""
    content = document.get('body').get('content')
    for element in content:
        if 'paragraph' in element:
            elements = element.get('paragraph').get('elements')
            for elem in elements:
                if 'textRun' in elem:
                    text += elem.get('textRun').get('content')
    return text

def parse_chapters(full_text: str):
    """
    Hàm sử dụng Regex để dò từng dòng, tìm chữ 'Chương X' 
    và cắt văn bản thành một danh sách các chương rõ ràng.
    """
    lines = full_text.split('\n')
    chapters = []
    
    current_chapter_num = None
    current_title = ""
    current_content = []

    # Regex: Bắt các dòng bắt đầu bằng chữ "Chương" kèm theo số
    chapter_pattern = re.compile(r"^Chương\s+(\d+)(.*)", re.IGNORECASE)

    for line in lines:
        match = chapter_pattern.match(line.strip())
        if match:
            # Nếu đã có dữ liệu của chương trước đó thì lưu lại
            if current_chapter_num is not None:
                chapters.append({
                    "chapter_number": current_chapter_num,
                    "title": current_title.strip(),
                    "content": "\n".join(current_content).strip()
                })
            
            # Bắt đầu thu thập chương mới
            current_chapter_num = int(match.group(1))
            current_title = f"Chương {current_chapter_num}{match.group(2)}"
            current_content = []
        else:
            # Nếu không phải là dòng tiêu đề, thì đây là nội dung truyện
            if current_chapter_num is not None:
                # Bỏ qua các dòng trống dư thừa ở đầu chương
                if line.strip() != "" or len(current_content) > 0:
                    current_content.append(line.strip())

    # Lưu lại chương cuối cùng sau khi vòng lặp kết thúc
    if current_chapter_num is not None:
        chapters.append({
            "chapter_number": current_chapter_num,
            "title": current_title.strip(),
            "content": "\n".join(current_content).strip()
        })

    return chapters