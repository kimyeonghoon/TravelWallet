"""
인증 및 보안 서비스

이 파일은 애플리케이션의 인증 시스템을 관리합니다.
텔레그램 봇을 통한 2FA 인증, JWT 토큰 관리, IP 기반 보안 기능을 제공합니다.

주요 기능:
- 텔레그램 봇을 통한 6자리 인증 코드 발송
- JWT 토큰 생성 및 검증
- IP 기반 로그인 시도 제한 (Rate Limiting)
- 사용자 인증 및 권한 관리

보안 특징:
- 이메일 기반 사전 승인 시스템
- 15분 토큰 만료로 보안 강화
- IP별 로그인 시도 횟수 제한 (5회 실패 시 10분 차단)
"""

# 표준 라이브러리 및 외부 라이브러리 임포트
import os
import secrets  # 안전한 랜덤 문자열 생성
import random  # 6자리 코드 생성용
import requests  # 텔레그램 API 호출
from datetime import datetime, timedelta  # 시간 관련 처리
from typing import Optional  # 타입 힌팅

# 외부 라이브러리
from dotenv import load_dotenv  # 환경변수 로딩
from jose import JWTError, jwt  # JWT 토큰 처리
from passlib.context import CryptContext  # 비밀번호 해싱 (미사용)
from sqlalchemy.orm import Session  # 데이터베이스 세션

# 자체 모듈
from models import User, LoginToken, IPBan  # 데이터베이스 모델

# 환경변수 로딩
load_dotenv()

# ==================== 설정 값 정의 ====================

# JWT 토큰 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")  # JWT 서명 키
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # JWT 암호화 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # 토큰 만료 시간 (15분)

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # 텔레그램 봇 토큰
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "일본 여행 경비 인증")  # 봇 이름
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5496782369")  # 고정 Chat ID
APP_URL = os.getenv("APP_URL", "http://localhost:8000")  # 애플리케이션 URL

# 인증 설정
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL", "me@yeonghoon.kim")  # 허용된 이메일 (사전 승인 시스템)
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
BAN_DURATION_MINUTES = int(os.getenv("BAN_DURATION_MINUTES", "10"))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for handling email-based Telegram bot login."""
    
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
    def check_ip_ban(db: Session, ip_address: str) -> Optional[IPBan]:
        """Check if IP address is banned."""
        ip_ban = db.query(IPBan).filter(IPBan.ip_address == ip_address).first()
        if ip_ban and ip_ban.is_banned():
            return ip_ban
        return None
    
    @staticmethod
    def record_failed_attempt(db: Session, ip_address: str) -> bool:
        """Record failed login attempt and ban IP if necessary."""
        ip_ban = db.query(IPBan).filter(IPBan.ip_address == ip_address).first()
        
        if not ip_ban:
            # First failed attempt
            ip_ban = IPBan(
                ip_address=ip_address,
                failed_attempts=1,
                first_attempt=datetime.utcnow(),
                last_attempt=datetime.utcnow()
            )
            db.add(ip_ban)
        else:
            # Update existing record
            ip_ban.failed_attempts += 1
            ip_ban.last_attempt = datetime.utcnow()
            
            # Ban IP if max attempts reached
            if ip_ban.failed_attempts >= MAX_LOGIN_ATTEMPTS:
                ip_ban.banned_until = datetime.utcnow() + timedelta(minutes=BAN_DURATION_MINUTES)
        
        db.commit()
        return ip_ban.failed_attempts >= MAX_LOGIN_ATTEMPTS
    
    @staticmethod
    def reset_failed_attempts(db: Session, ip_address: str):
        """Reset failed attempts for successful login."""
        ip_ban = db.query(IPBan).filter(IPBan.ip_address == ip_address).first()
        if ip_ban:
            db.delete(ip_ban)
            db.commit()
    
    @staticmethod
    def verify_email_and_send_code(db: Session, email: str, ip_address: str) -> tuple[bool, str]:
        """Verify email and send Telegram code if valid."""
        # Verify email first
        if email.lower() != ALLOWED_EMAIL.lower():
            # Check if IP is banned before recording failed attempt
            ip_ban = AuthService.check_ip_ban(db, ip_address)
            if ip_ban:
                remaining_time = int((ip_ban.banned_until - datetime.utcnow()).total_seconds() / 60)
                return False, f"IP가 차단되었습니다. {remaining_time}분 후 다시 시도하세요."
            
            # Record failed attempt for wrong email
            is_banned = AuthService.record_failed_attempt(db, ip_address)
            if is_banned:
                return False, f"너무 많은 실패로 인해 {BAN_DURATION_MINUTES}분간 접속이 제한됩니다."
            return False, "등록되지 않은 이메일입니다."
        
        # Email is valid - reset any previous failures and IP bans
        AuthService.reset_failed_attempts(db, ip_address)
        
        # Get or create user with configured Chat ID
        user = AuthService.create_user(db, TELEGRAM_CHAT_ID)
        
        # Create and send login code
        login_token = AuthService.create_login_code(db, user.id)
        success = AuthService.send_login_code_telegram(user.telegram_chat_id, login_token.token)
        
        if success:
            return True, "인증 코드가 텔레그램으로 전송되었습니다."
        else:
            return True, "인증 코드가 생성되었습니다. (개발 모드)"
    
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