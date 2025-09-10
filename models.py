from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pytz
import os

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def now_kst():
    """현재 한국 시간을 반환"""
    return datetime.now(KST)

Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)  # 지갑 선택 (optional)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(200), default="")
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    payment_method = Column(String(20), nullable=False, default="현금")  # 현금, 체크카드, 신용카드, 교통카드
    timestamp = Column(DateTime, default=now_kst)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    wallet = relationship("Wallet", back_populates="expenses")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "wallet_id": self.wallet_id,
            "wallet_name": self.wallet.name if self.wallet else None,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date,
            "payment_method": self.payment_method,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_chat_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)  # Keep for backward compatibility
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_kst)
    last_login = Column(DateTime, nullable=True)
    last_login_request = Column(DateTime, nullable=True)
    
    # Relationship to expenses
    expenses = relationship("Expense", back_populates="user")
    login_tokens = relationship("LoginToken", back_populates="user")
    
    def to_dict(self):
        return {
            "id": self.id,
            "telegram_chat_id": self.telegram_chat_id,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
        }

class LoginToken(Base):
    __tablename__ = "login_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now_kst)
    
    # Relationship
    user = relationship("User", back_populates="login_tokens")

class TransportCard(Base):
    __tablename__ = "transport_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Card name (e.g., "Suica", "PASMO")
    balance = Column(Float, nullable=False, default=0.0)  # Balance in Japanese Yen
    created_at = Column(DateTime, default=now_kst)
    updated_at = Column(DateTime, default=now_kst, onupdate=now_kst)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "balance": self.balance,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Wallet name (e.g., "일본지갑", "메인지갑", "여권지갑")
    balance = Column(Float, nullable=False, default=0.0)  # Balance in Japanese Yen
    created_at = Column(DateTime, default=now_kst)
    updated_at = Column(DateTime, default=now_kst, onupdate=now_kst)
    
    # Relationship
    expenses = relationship("Expense", back_populates="wallet")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "balance": self.balance,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

class IPBan(Base):
    __tablename__ = "ip_bans"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), index=True, nullable=False)  # Support IPv6
    failed_attempts = Column(Integer, default=1)
    banned_until = Column(DateTime, nullable=True)
    first_attempt = Column(DateTime, default=now_kst)
    last_attempt = Column(DateTime, default=now_kst)
    
    def is_banned(self):
        """Check if IP is currently banned."""
        if self.banned_until and now_kst() < self.banned_until:
            return True
        return False

# Database configuration
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./japan_travel_expenses.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()