from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import verify_token, create_access_token, get_password_hash, verify_password

import sqlite3
import os
import datetime
import jwt
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passlib.context import CryptContext
from fastapi.responses import FileResponse
from transformers import pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://c0d3g3n.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

conn = sqlite3.connect("conversions.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
""")
conn.commit()

logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s - %(message)s")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"

def send_email(to_email, subject, message):
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logging.info(f"{request.method} {request.url} - {response.status_code}")
    return response

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@app.post("/password-reset/")
async def request_password_reset(data: PasswordResetRequest):
    cursor.execute("SELECT id FROM users WHERE email = ?", (data.email,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=400, detail="E-mail niet gevonden")
    
    reset_token = jwt.encode({"sub": user[0], "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)}, SECRET_KEY, algorithm=ALGORITHM)
    reset_link = f"https://c0d3g3n.com/reset-password?token={reset_token}"
    send_email(data.email, "Wachtwoord reset", f"Klik hier om je wachtwoord te resetten: {reset_link}")

    return {"message": "Resetlink is verzonden naar je e-mail"}

@app.post("/password-reset/confirm/")
async def confirm_password_reset(data: PasswordResetConfirm):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        hashed_password = get_password_hash(data.new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        return {"message": "Wachtwoord succesvol gewijzigd"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token is verlopen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Ongeldig token")

@app.delete("/admin/delete-user/{user_id}")
async def delete_user(user_id: int, admin_id: int = Depends(verify_token)):
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (admin_id,))
    admin = cursor.fetchone()
    if not admin or admin[0] == 0:
        raise HTTPException(status_code=403, detail="Geen admin-rechten")
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"message": "Gebruiker verwijderd"}

@app.put("/admin/set-admin/{user_id}")
async def set_admin_status(user_id: int, is_admin: bool, admin_id: int = Depends(verify_token)):
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (admin_id,))
    admin = cursor.fetchone()
    if not admin or admin[0] == 0:
        raise HTTPException(status_code=403, detail="Geen admin-rechten")
    cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))
    conn.commit()
    return {"message": f"Gebruiker {'is nu admin' if is_admin else 'is geen admin meer'}"}

@app.get("/")
def read_root():
    return {"message": "API werkt correct!"}
