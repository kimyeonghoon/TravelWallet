import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import User, LoginToken

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for handling email-based login."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def create_user(db: Session, email: str) -> User:
        """Create a new user or return existing user."""
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.last_login_request = datetime.utcnow()
            db.commit()
            return user
        
        user = User(
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login_request=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_login_token(db: Session, user_id: int) -> LoginToken:
        """Create a magic link login token."""
        # Invalidate any existing tokens for this user
        db.query(LoginToken).filter(LoginToken.user_id == user_id).update({"is_used": True})
        
        token = LoginToken(
            user_id=user_id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            is_used=False
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token
    
    @staticmethod
    def validate_login_token(db: Session, token: str) -> Optional[User]:
        """Validate magic link token and return user if valid."""
        login_token = db.query(LoginToken).filter(
            LoginToken.token == token,
            LoginToken.is_used == False,
            LoginToken.expires_at > datetime.utcnow()
        ).first()
        
        if not login_token:
            return None
        
        # Mark token as used
        login_token.is_used = True
        login_token.used_at = datetime.utcnow()
        
        # Update user's last login
        user = db.query(User).filter(User.id == login_token.user_id).first()
        if user:
            user.last_login = datetime.utcnow()
        
        db.commit()
        return user
    
    @staticmethod
    def send_magic_link_email(email: str, magic_link: str) -> bool:
        """Send magic link email to user."""
        if not all([SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL]):
            print("Email configuration not set. Magic link:", magic_link)
            return True  # For development without email setup
        
        try:
            # Create email content
            subject = "일본 여행 경비 - 로그인 링크"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; background-color: #f8f9fa; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🇯🇵 일본 여행 경비 추적기</h2>
                    </div>
                    <div class="content">
                        <h3>안녕하세요!</h3>
                        <p>일본 여행 경비 추적기에 로그인하려면 아래 버튼을 클릭해주세요.</p>
                        <div style="text-align: center;">
                            <a href="{magic_link}" class="button">로그인하기</a>
                        </div>
                        <p><strong>보안을 위해 이 링크는 15분 후 만료됩니다.</strong></p>
                        <p>이 요청을 하지 않으셨다면 이 이메일을 무시하셔도 됩니다.</p>
                        <hr>
                        <p style="font-size: 12px; color: #666;">링크가 작동하지 않는다면 아래 URL을 복사하여 브라우저에 붙여넣으세요:</p>
                        <p style="word-break: break-all; font-size: 12px;">{magic_link}</p>
                    </div>
                    <div class="footer">
                        <p>일본 여행 경비 추적기 🎌</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = email
            
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            print(f"Magic link for development: {magic_link}")
            return False