import os
import secrets
import random
import requests
from datetime import datetime, timedelta
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

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "일본 여행 경비 인증")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for handling Telegram bot-based login."""
    
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
    def create_user(db: Session, telegram_chat_id: str) -> User:
        """Create a new user or return existing user by Telegram chat ID."""
        user = db.query(User).filter(User.telegram_chat_id == telegram_chat_id).first()
        if user:
            user.last_login_request = datetime.utcnow()
            db.commit()
            return user
        
        user = User(
            telegram_chat_id=telegram_chat_id,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login_request=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_login_code(db: Session, user_id: int) -> LoginToken:
        """Create a numeric login code."""
        # Invalidate any existing tokens for this user
        db.query(LoginToken).filter(LoginToken.user_id == user_id).update({"is_used": True})
        
        # Generate 6-digit numeric code
        code = f"{random.randint(100000, 999999)}"
        
        token = LoginToken(
            user_id=user_id,
            token=code,
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            is_used=False
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token
    
    @staticmethod
    def validate_login_code(db: Session, code: str) -> Optional[User]:
        """Validate numeric login code and return user if valid."""
        login_token = db.query(LoginToken).filter(
            LoginToken.token == code,
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
    def send_login_code_telegram(chat_id: str, code: str) -> bool:
        """Send login code via Telegram bot."""
        if not TELEGRAM_BOT_TOKEN:
            print("Telegram bot token not set. Login code:", code)
            print(f"Chat ID: {chat_id}")
            return True  # For development without bot setup
        
        try:
            # Telegram Bot API URL
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Message content
            message = f"""🇯🇵 일본 여행 경비 추적기

🔐 로그인 코드: {code}

이 코드를 웹사이트에 입력하여 로그인하세요.

⏰ 코드는 15분 후 만료됩니다.
🚫 요청하지 않으셨다면 이 메시지를 무시하세요."""

            # Send message
            payload = {
                'chat_id': chat_id,
                'text': message
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Telegram message: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            print(f"Login code for development: {code}")
            print(f"Chat ID: {chat_id}")
            return False
        except Exception as e:
            print(f"Unexpected error sending Telegram message: {e}")
            print(f"Login code for development: {code}")
            print(f"Chat ID: {chat_id}")
            return False