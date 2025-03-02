from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import os
import datetime
import jwt
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from transformers import pipeline

# 🔧 Load environment variables (.env file support)
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

app = FastAPI()

# ✅ CORS Setup (Allow only frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://c0d3g3n.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ✅ Database Connection
conn = sqlite3.connect("conversions.db", check_same_thread=False)
cursor = conn.cursor()

# ✅ Create Users Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
""")

# ✅ Create Conversions Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        legacy_code TEXT NOT NULL,
        source_language TEXT NOT NULL,
        target_language TEXT NOT NULL,
        modern_code TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
""")

# ✅ Create Feedback Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        conversion_id INTEGER,
        comments TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
""")
conn.commit()

# ✅ Logging Configuration
logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# 🔑 Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


import jwt

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
    to_encode.update({"exp": expire})

    # Ensure you have the correct secret key and algorithm
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"

    # Correct way to encode the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Geen token meegegeven")
    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is verlopen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Ongeldige token")


# 📧 **Send Email Function**
def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    except Exception as e:
        logging.error(f"❌ Email sending failed: {e}")


# 📜 **Middleware for Logging Requests**
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logging.info(f"{request.method} {request.url} - {response.status_code}")
    return response


# 📌 **User Models**
class RegisterInput(BaseModel):
    username: str
    password: str
    email: EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class CodeInput(BaseModel):
    legacy_code: str
    source_language: str
    target_language: str


class FeedbackRequest(BaseModel):
    user_id: int
    conversion_id: int
    feedback: str


# ✅ **User Registration**
@app.post("/register/")
async def register_user(data: RegisterInput):
    hashed_password = get_password_hash(data.password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)", (data.username, hashed_password, data.email))
        conn.commit()
        return {"message": "Gebruiker succesvol geregistreerd!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Gebruikersnaam of e-mail bestaat al")


# ✅ **User Login**
@app.post("/login/")
async def login_user(data: LoginRequest):
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (data.username,))
    user = cursor.fetchone()
    if not user or not verify_password(data.password, user[1]):
        raise HTTPException(status_code=400, detail="Ongeldige login")
    access_token = create_access_token(data={"sub": str(user[0])}, expires_delta=datetime.timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}


# ✅ **Code Conversion**
@app.post("/convert/")
async def convert_code(data: CodeInput, user: str = Depends(verify_token)):
    modern_code = f"// Converted from {data.source_language} to {data.target_language}\n{data.legacy_code}"  # Mock conversion
    cursor.execute(
        "INSERT INTO conversions (user_id, legacy_code, source_language, target_language, modern_code) VALUES (?, ?, ?, ?, ?)",
        (user, data.legacy_code, data.source_language, data.target_language, modern_code)
    )
    conn.commit()
    return {"modern_code": modern_code}


# ✅ **Get Conversion History**
@app.get("/history/")
async def get_conversion_history(user_id: int = Depends(verify_token)):
    cursor.execute("SELECT * FROM conversions WHERE user_id = ?", (user_id,))
    conversions = cursor.fetchall()
    return {"history": [{"id": conv[0], "legacy_code": conv[2], "target_language": conv[4]} for conv in conversions]}


# ✅ **Submit Feedback**
@app.post("/feedback/")
async def submit_feedback(feedback: FeedbackRequest):
    cursor.execute("INSERT INTO feedback (user_id, conversion_id, comments) VALUES (?, ?, ?)",
                   (feedback.user_id, feedback.conversion_id, feedback.feedback))
    conn.commit()
    return {"message": "Feedback opgeslagen"}


# ✅ **Health Check**
@app.get("/")
def read_root():
    return {"message": "API werkt correct!"}
