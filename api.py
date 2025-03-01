import os
import psycopg2
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import jwt
from passlib.context import CryptContext
from transformers import pipeline

# Initialize FastAPI app
app = FastAPI()

# Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize the AI code conversion model
code_converter = pipeline("text2text-generation", model="facebook/bart-large")

def convert_code(legacy_code: str, source_lang: str, target_lang: str) -> str:
    """
    Convert legacy code to a modern language using AI.
    """
    prompt = f"Convert {source_lang} code to {target_lang}: \n{legacy_code}"
    output = code_converter(prompt, max_length=500)
    return output[0]['generated_text']

# Use environment variable for PostgreSQL connection; adjust defaults as needed.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://youruser:yourpassword@localhost:5432/codegen")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_tables():
    """Create database tables in PostgreSQL if they do not exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS conversions (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            legacy_code TEXT NOT NULL,
                            source_language TEXT NOT NULL,
                            target_language TEXT NOT NULL,
                            modern_code TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            original_code TEXT NOT NULL,
                            converted_code TEXT NOT NULL,
                            rating INTEGER NOT NULL,
                            comments TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()

create_tables()

# JWT & Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "supersecretkey"  # Replace with a secure key in production
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Token not provided")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Invalid authorization header format")
    token = authorization[len("Bearer "):].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")

# Data Models
class RegisterInput(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CodeInput(BaseModel):
    legacy_code: str
    source_language: str
    target_language: str

class FeedbackRequest(BaseModel):
    user_id: int
    original_code: str
    converted_code: str
    rating: int  # 1 = Poor, 5 = Excellent
    comments: str = None

# Health Check Endpoints
@app.get("/", tags=["Health"])
def read_root():
    return {"message": "API is working correctly!"}

@app.get("/healthcheck", tags=["Health"])
async def healthcheck():
    return {"message": "API is working correctly!"}

# Authentication Endpoints
@app.post("/register/", tags=["Authentication"])
async def register(user: RegisterInput):
    hashed_password = get_password_hash(user.password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (user.username, hashed_password)
        )
        conn.commit()
        return {"message": "User registered successfully!"}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/login/", tags=["Authentication"])
async def login(credentials: LoginRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (credentials.username,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=400, detail="Invalid username or password")
        user_id, password_hash = user
        if not verify_password(credentials.password, password_hash):
            raise HTTPException(status_code=400, detail="Invalid username or password")
        access_token = create_access_token(data={"sub": str(user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        cursor.close()
        conn.close()

# Code Conversion Endpoint
@app.post("/convert/", tags=["Conversion"])
async def convert(input_data: CodeInput, user_id: int = Depends(verify_token)):
    try:
        modern_code = convert_code(input_data.legacy_code, input_data.source_language, input_data.target_language)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversions (user_id, legacy_code, source_language, target_language, modern_code) VALUES (%s, %s, %s, %s, %s)",
                (user_id, input_data.legacy_code, input_data.source_language, input_data.target_language, modern_code)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return {"modern_code": modern_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

# Conversion History Endpoint
@app.get("/history/", tags=["History"])
async def get_conversion_history(user_id: int = Depends(verify_token)):
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, legacy_code, source_language, target_language, modern_code, created_at FROM conversions WHERE user_id = %s",
                (user_id,)
            )
            conversions = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        history = [
            {
                "id": conv[0],
                "legacy_code": conv[1],
                "source_language": conv[2],
                "target_language": conv[3],
                "modern_code": conv[4],
                "created_at": str(conv[5]) if conv[5] is not None else None
            }
            for conv in conversions
        ]
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Feedback Submission Endpoint
@app.post("/feedback/", tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest, user_id: int = Depends(verify_token)):
    if user_id != feedback.user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (user_id, original_code, converted_code, rating, comments) VALUES (%s, %s, %s, %s, %s)",
                (feedback.user_id, feedback.original_code, feedback.converted_code, feedback.rating, feedback.comments)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return {"message": "Feedback saved successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")
