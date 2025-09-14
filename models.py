"""
일본 여행 경비 추적 애플리케이션 데이터베이스 모델

이 파일은 SQLAlchemy ORM을 사용하여 데이터베이스 테이블 구조를 정의합니다.

주요 테이블:
- users: 사용자 정보 (텔레그램 인증)
- trips: 여행 정보 (여행명, 기간 등)
- expenses: 지출 내역
- transport_cards: 교통카드 정보
- wallets: 엔화 지갑 정보
"""

# SQLAlchemy ORM 관련 임포트
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine, func
from sqlalchemy.ext.declarative import declarative_base  # 모델 베이스 클래스
from sqlalchemy.orm import sessionmaker, relationship  # 세션 및 관계 설정
from datetime import datetime
import pytz  # 시간대 처리
import os

# 한국 시간대 설정 (서버 시간대와 관계없이 일관된 시간 처리)
KST = pytz.timezone('Asia/Seoul')

def now_kst():
    """현재 한국 시간을 반환하는 유틸리티 함수"""
    return datetime.now(KST)

# SQLAlchemy 모델 베이스 클래스
Base = declarative_base()

class Trip(Base):
    """
    여행 정보 테이블
    개별 여행의 기본 정보를 관리
    """
    __tablename__ = "trips"

    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)  # 여행 고유 ID

    # 여행 정보
    name = Column(String(100), nullable=False)  # 여행 이름 (예: "2025년 일본 여행")
    destination = Column(String(100), nullable=False)  # 여행지 (예: "일본")
    start_date = Column(String(10), nullable=False)  # 시작일 (YYYY-MM-DD 형식)
    end_date = Column(String(10), nullable=False)  # 종료일 (YYYY-MM-DD 형식)
    description = Column(String(500), default="")  # 여행 설명
    is_default = Column(Boolean, default=False)  # 기본 여행 여부
    created_at = Column(DateTime, default=now_kst)  # 생성 시간
    updated_at = Column(DateTime, default=now_kst, onupdate=now_kst)  # 수정 시간

    # 테이블 간 관계 설정
    expenses = relationship("Expense", back_populates="trip")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "is_default": self.is_default,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

class Expense(Base):
    """
    지출 내역 테이블
    사용자의 여행 중 지출을 기록하는 메인 테이블
    """
    __tablename__ = "expenses"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)  # 지출 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 사용자 ID (하위 호환성을 위해 nullable)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)  # 여행 ID (하위 호환성을 위해 nullable)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)  # 현금 결제 시 사용한 지갑 ID (선택사항)
    
    # 지출 정보
    amount = Column(Float, nullable=False)  # 지출 금액 (원화)
    category = Column(String(50), nullable=False)  # 카테고리 (식비, 교통비, 숙박비, 입장료, 기타)
    description = Column(String(200), default="")  # 지출 설명
    date = Column(String(10), nullable=False)  # 지출 날짜 (YYYY-MM-DD 형식)
    payment_method = Column(String(20), nullable=False, default="현금")  # 결제 수단
    timestamp = Column(DateTime, default=now_kst)  # 등록 시간 (한국 시간)
    
    # 테이블 간 관계 설정
    user = relationship("User", back_populates="expenses")
    trip = relationship("Trip", back_populates="expenses")
    wallet = relationship("Wallet", back_populates="expenses")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trip_id": self.trip_id,
            "trip_name": self.trip.name if self.trip else None,
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
    transportations = relationship("Transportation", back_populates="user")
    
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
    """
    로그인 토큰 테이블
    텔레그램 인증 시 사용되는 6자리 코드를 관리
    """
    __tablename__ = "login_tokens"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)  # 토큰 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID
    
    # 토큰 정보
    token = Column(String(255), unique=True, index=True, nullable=False)  # 6자리 인증 코드
    expires_at = Column(DateTime, nullable=False)  # 토큰 만료 시간 (15분)
    is_used = Column(Boolean, default=False)  # 사용 여부
    used_at = Column(DateTime, nullable=True)  # 사용된 시간
    created_at = Column(DateTime, default=now_kst)  # 생성 시간
    
    # 테이블 간 관계
    user = relationship("User", back_populates="login_tokens")

class TransportCard(Base):
    """
    교통카드 정보 테이블
    일본 교통카드(스이카, 파스모 등)의 잔액을 관리
    """
    __tablename__ = "transport_cards"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)  # 교통카드 고유 ID
    
    # 교통카드 정보
    name = Column(String(100), nullable=False)  # 카드 이름 (예: "스이카", "파스모")
    balance = Column(Float, nullable=False, default=0.0)  # 잔액 (일본 엔화)
    created_at = Column(DateTime, default=now_kst)  # 생성 시간
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

class Transportation(Base):
    """
    교통수단 이용 기록 테이블
    일본 여행 중 이용한 교통수단 정보를 기록
    """
    __tablename__ = "transportation"

    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)  # 교통수단 기록 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 사용자 ID (하위 호환성을 위해 nullable)

    # 교통수단 정보
    category = Column(String(20), nullable=False)  # 교통수단 카테고리 (JR, 전철, 버스, 배, 기타)
    company = Column(String(50), default="")  # 이용회사 (서일본, 히로덴 등)
    departure_time = Column(String(5), nullable=False)  # 출발시간 (HH:MM)
    arrival_time = Column(String(5), nullable=False)  # 도착시간 (HH:MM)
    memo = Column(String(200), default="")  # 메모 (출발지-도착지, 노선 등)
    date = Column(String(10), nullable=False)  # 이용 날짜 (YYYY-MM-DD 형식)
    timestamp = Column(DateTime, default=now_kst)  # 등록 시간 (한국 시간)

    # 테이블 간 관계 설정
    user = relationship("User", back_populates="transportations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "company": self.company,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "memo": self.memo,
            "date": self.date,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/japan_travel_expenses.db")
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