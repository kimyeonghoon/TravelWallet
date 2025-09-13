"""
데이터베이스 서비스 레이어

이 파일은 데이터베이스 CRUD(Create, Read, Update, Delete) 작업을 처리하는
서비스 클래스들을 정의합니다. 각 테이블(지출, 교통카드, 지갑)에 대한
비즈니스 로직과 데이터 액세스 로직을 포함합니다.

주요 서비스:
- ExpenseService: 지출 내역 관리
- TransportCardService: 교통카드 관리  
- WalletService: 엔화 지갑 관리
"""

# SQLAlchemy 및 관련 라이브러리 임포트
from sqlalchemy.orm import Session, selectinload  # 데이터베이스 세션 및 관계 로딩
from sqlalchemy import func  # SQL 함수 (COUNT, SUM 등)
from models import Expense, TransportCard, Wallet, Transportation, now_kst  # 데이터베이스 모델 및 한국 시간 함수
from datetime import datetime, date  # 날짜/시간 처리
from typing import List, Optional  # 타입 힌팅

class ExpenseService:
    """
    지출 내역 관리 서비스
    지출 데이터의 생성, 조회, 수정, 삭제 및 통계 기능을 제공
    """
    
    @staticmethod
    def create_expense(db: Session, user_id: int, amount: float, category: str, description: str = "", payment_method: str = "현금", wallet_id: int = None) -> Expense:
        """
        새로운 지출 내역을 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            amount: 지출 금액 (원화)
            category: 지출 카테고리
            description: 지출 설명
            payment_method: 결제 수단
            wallet_id: 지갑 ID (현금 결제 시 선택사항)
            
        Returns:
            생성된 지출 객체
        """
        expense = Expense(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            category=category,
            description=description,
            date=date.today().strftime("%Y-%m-%d"),
            payment_method=payment_method,
            timestamp=now_kst()
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
    
    @staticmethod
    def get_all_expenses(db: Session) -> List[Expense]:
        """Get all expenses ordered by timestamp descending."""
        return db.query(Expense).options(selectinload(Expense.wallet)).order_by(Expense.timestamp.desc()).all()
    
    @staticmethod
    def get_expense(db: Session, expense_id: int) -> Optional[Expense]:
        """Get a single expense by ID."""
        return db.query(Expense).filter(Expense.id == expense_id).first()
    
    @staticmethod
    def delete_expense(db: Session, expense_id: int) -> bool:
        """Delete an expense by ID."""
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            db.delete(expense)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_expenses_by_date(db: Session, target_date: str) -> List[Expense]:
        """Get expenses for a specific date (YYYY-MM-DD format)."""
        return db.query(Expense).filter(Expense.date == target_date).all()
    
    @staticmethod
    def get_expenses_by_category(db: Session, category: str) -> List[Expense]:
        """Get expenses for a specific category."""
        return db.query(Expense).filter(Expense.category == category).all()
    
    @staticmethod
    def get_total_expenses(db: Session) -> float:
        """Get total amount of all expenses."""
        result = db.query(func.sum(Expense.amount)).scalar()
        return result if result else 0.0
    
    @staticmethod
    def get_today_expenses_total(db: Session) -> float:
        """Get total expenses for today."""
        today = date.today().strftime("%Y-%m-%d")
        result = db.query(func.sum(Expense.amount)).filter(Expense.date == today).scalar()
        return result if result else 0.0
    
    @staticmethod
    def get_filtered_expenses(
        db: Session, 
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        search: Optional[str] = None
    ) -> List[Expense]:
        """Get expenses with optional filters and sorting."""
        query = db.query(Expense).options(selectinload(Expense.wallet))
        
        # Apply filters
        if category:
            query = query.filter(Expense.category == category)
        
        if payment_method:
            query = query.filter(Expense.payment_method == payment_method)
        
        if date_from:
            query = query.filter(Expense.date >= date_from)
        
        if date_to:
            query = query.filter(Expense.date <= date_to)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(Expense.description.ilike(search_term))
        
        # Apply sorting
        if sort_by == "date":
            if sort_order == "asc":
                query = query.order_by(Expense.date.asc(), Expense.timestamp.asc())
            else:
                query = query.order_by(Expense.date.desc(), Expense.timestamp.desc())
        elif sort_by == "amount":
            if sort_order == "asc":
                query = query.order_by(Expense.amount.asc())
            else:
                query = query.order_by(Expense.amount.desc())
        else:
            # Default sorting: newest first
            query = query.order_by(Expense.timestamp.desc())
        
        return query.all()
    
    @staticmethod
    def get_statistics(db: Session) -> dict:
        """Get comprehensive statistics for dashboard."""
        from collections import defaultdict
        
        # Get all expenses
        expenses = db.query(Expense).all()
        
        if not expenses:
            return {
                "category_stats": {},
                "payment_method_stats": {},
                "daily_stats": [],
                "monthly_stats": [],
                "weekly_stats": {},
                "top_expenses": [],
                "avg_daily": 0,
                "total_days": 0,
                "expense_count": 0
            }
        
        # Category statistics
        category_stats = defaultdict(lambda: {"count": 0, "amount": 0})
        for expense in expenses:
            category_stats[expense.category]["count"] += 1
            category_stats[expense.category]["amount"] += expense.amount
        
        # Payment method statistics  
        payment_method_stats = defaultdict(lambda: {"count": 0, "amount": 0})
        for expense in expenses:
            payment_method_stats[expense.payment_method]["count"] += 1
            payment_method_stats[expense.payment_method]["amount"] += expense.amount
        
        # Daily statistics (last 30 days)
        daily_stats = defaultdict(float)
        for expense in expenses:
            daily_stats[expense.date] += expense.amount
        
        # Convert to list of dicts sorted by date
        daily_list = [{"date": date, "amount": amount} for date, amount in sorted(daily_stats.items())]
        
        # Monthly statistics
        monthly_stats = defaultdict(float)
        for expense in expenses:
            month_key = expense.date[:7]  # YYYY-MM
            monthly_stats[month_key] += expense.amount
        
        monthly_list = [{"month": month, "amount": amount} for month, amount in sorted(monthly_stats.items())]
        
        # Weekly statistics (day of week)
        from datetime import datetime
        weekly_stats = defaultdict(float)
        for expense in expenses:
            expense_date = datetime.strptime(expense.date, "%Y-%m-%d")
            day_name = expense_date.strftime("%A")
            weekly_stats[day_name] += expense.amount
        
        # Top 10 expenses
        top_expenses = sorted(expenses, key=lambda x: x.amount, reverse=True)[:10]
        top_expenses_list = [{
            "amount": exp.amount,
            "category": exp.category,
            "description": exp.description,
            "date": exp.date,
            "payment_method": exp.payment_method
        } for exp in top_expenses]
        
        # Calculate averages
        unique_dates = len(set(exp.date for exp in expenses))
        total_amount = sum(exp.amount for exp in expenses)
        avg_daily = total_amount / unique_dates if unique_dates > 0 else 0
        
        return {
            "category_stats": dict(category_stats),
            "payment_method_stats": dict(payment_method_stats),
            "daily_stats": daily_list,
            "monthly_stats": monthly_list,
            "weekly_stats": dict(weekly_stats),
            "top_expenses": top_expenses_list,
            "avg_daily": round(avg_daily, 2),
            "total_days": unique_dates,
            "expense_count": len(expenses),
            "total_amount": total_amount
        }
    
    @staticmethod
    def update_expense(db: Session, expense_id: int, amount: float = None, 
                      category: str = None, description: str = None, 
                      expense_date: str = None, expense_time: str = None,
                      payment_method: str = None, wallet_id: int = None) -> Optional[Expense]:
        """Update an expense by ID."""
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            if amount is not None:
                expense.amount = amount
            if category is not None:
                expense.category = category
            if description is not None:
                expense.description = description
            if expense_date is not None:
                expense.date = expense_date
            if payment_method is not None:
                expense.payment_method = payment_method
            if wallet_id is not None:
                expense.wallet_id = wallet_id
            if expense_time is not None:
                # Parse time and combine with existing date or new date
                try:
                    from datetime import datetime
                    time_parts = expense_time.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Use the current date if no date change, otherwise use new date
                    current_date = expense_date if expense_date else expense.date
                    new_datetime = datetime.strptime(f"{current_date} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
                    expense.timestamp = new_datetime
                except (ValueError, IndexError):
                    # If time parsing fails, keep original timestamp
                    pass
            
            db.commit()
            db.refresh(expense)
            return expense
        return None
    
    # User-specific methods
    @staticmethod
    def get_user_expenses(db: Session, user_id: int) -> List[Expense]:
        """Get all expenses for a specific user ordered by timestamp descending."""
        return db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.timestamp.desc()).all()
    
    @staticmethod
    def get_user_expense(db: Session, user_id: int, expense_id: int) -> Optional[Expense]:
        """Get a single expense by ID for a specific user."""
        return db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
    
    @staticmethod
    def update_user_expense(db: Session, user_id: int, expense_id: int, amount: float = None, 
                          category: str = None, description: str = None, 
                          expense_date: str = None, expense_time: str = None,
                          payment_method: str = None, wallet_id: int = None) -> Optional[Expense]:
        """Update an expense by ID for a specific user."""
        expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
        if expense:
            if amount is not None:
                expense.amount = amount
            if category is not None:
                expense.category = category
            if description is not None:
                expense.description = description
            if payment_method is not None:
                expense.payment_method = payment_method
            if wallet_id is not None:
                expense.wallet_id = wallet_id
            if expense_date is not None:
                expense.date = expense_date
            if expense_time is not None:
                # Parse time and combine with existing date or new date
                try:
                    from datetime import datetime
                    time_parts = expense_time.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Use the current date if no date change, otherwise use new date
                    current_date = expense_date if expense_date else expense.date
                    new_datetime = datetime.strptime(f"{current_date} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
                    expense.timestamp = new_datetime
                except (ValueError, IndexError):
                    # If time parsing fails, keep original timestamp
                    pass
            
            db.commit()
            db.refresh(expense)
            return expense
        return None
    
    @staticmethod
    def delete_user_expense(db: Session, user_id: int, expense_id: int) -> bool:
        """Delete an expense by ID for a specific user."""
        expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
        if expense:
            db.delete(expense)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_total_expenses(db: Session, user_id: int) -> float:
        """Get total amount of all expenses for a specific user."""
        result = db.query(func.sum(Expense.amount)).filter(Expense.user_id == user_id).scalar()
        return result if result else 0.0
    
    @staticmethod
    def get_user_today_expenses_total(db: Session, user_id: int) -> float:
        """Get total expenses for today for a specific user."""
        today = date.today().strftime("%Y-%m-%d")
        result = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.date == today
        ).scalar()
        return result if result else 0.0


class TransportCardService:
    """Service class for transport card database operations."""
    
    @staticmethod
    def create_card(db: Session, name: str, balance: float = 0.0) -> TransportCard:
        """Create a new transport card."""
        card = TransportCard(
            name=name,
            balance=balance,
            created_at=now_kst(),
            updated_at=now_kst()
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        return card
    
    @staticmethod
    def get_all_cards(db: Session) -> List[TransportCard]:
        """Get all transport cards ordered by name."""
        return db.query(TransportCard).order_by(TransportCard.name).all()
    
    @staticmethod
    def get_card(db: Session, card_id: int) -> Optional[TransportCard]:
        """Get a single transport card by ID."""
        return db.query(TransportCard).filter(TransportCard.id == card_id).first()
    
    @staticmethod
    def update_card(db: Session, card_id: int, name: str = None, balance: float = None) -> Optional[TransportCard]:
        """Update a transport card."""
        card = db.query(TransportCard).filter(TransportCard.id == card_id).first()
        if card:
            if name is not None:
                card.name = name
            if balance is not None:
                card.balance = balance
            card.updated_at = now_kst()
            
            db.commit()
            db.refresh(card)
            return card
        return None
    
    @staticmethod
    def delete_card(db: Session, card_id: int) -> bool:
        """Delete a transport card by ID."""
        card = db.query(TransportCard).filter(TransportCard.id == card_id).first()
        if card:
            db.delete(card)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_total_balance(db: Session) -> float:
        """Get total balance of all transport cards."""
        result = db.query(func.sum(TransportCard.balance)).scalar()
        return result if result else 0.0

class WalletService:
    """Service class for wallet database operations."""

    @staticmethod
    def create_wallet(db: Session, name: str, balance: float = 0.0) -> Wallet:
        """Create a new wallet."""
        wallet = Wallet(
            name=name,
            balance=balance,
            created_at=now_kst(),
            updated_at=now_kst()
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return wallet

    @staticmethod
    def get_all_wallets(db: Session) -> List[Wallet]:
        """Get all wallets ordered by name."""
        return db.query(Wallet).order_by(Wallet.name).all()

    @staticmethod
    def get_wallet(db: Session, wallet_id: int) -> Optional[Wallet]:
        """Get a single wallet by ID."""
        return db.query(Wallet).filter(Wallet.id == wallet_id).first()

    @staticmethod
    def update_wallet(db: Session, wallet_id: int, name: str = None, balance: float = None) -> Optional[Wallet]:
        """Update a wallet."""
        wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if wallet:
            if name is not None:
                wallet.name = name
            if balance is not None:
                wallet.balance = balance
            wallet.updated_at = now_kst()

            db.commit()
            db.refresh(wallet)
            return wallet
        return None

    @staticmethod
    def delete_wallet(db: Session, wallet_id: int) -> bool:
        """Delete a wallet by ID."""
        wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if wallet:
            db.delete(wallet)
            db.commit()
            return True
        return False

    @staticmethod
    def get_total_balance(db: Session) -> float:
        """Get total balance of all wallets."""
        result = db.query(func.sum(Wallet.balance)).scalar()
        return result if result else 0.0

class TransportationService:
    """
    교통수단 이용 기록 관리 서비스
    교통수단 데이터의 생성, 조회, 수정, 삭제 기능을 제공
    """

    @staticmethod
    def create_transportation(db: Session, user_id: int, category: str, departure_time: str,
                             arrival_time: str, memo: str = "", company: str = "") -> Transportation:
        """
        새로운 교통수단 이용 기록을 생성합니다.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            category: 교통수단 카테고리 (JR, 전철, 버스, 배, 기타)
            departure_time: 출발시간 (HH:MM)
            arrival_time: 도착시간 (HH:MM)
            memo: 메모 (출발지-도착지, 노선 등)
            company: 이용회사 (서일본, 히로덴 등)

        Returns:
            생성된 교통수단 기록 객체
        """
        transportation = Transportation(
            user_id=user_id,
            category=category,
            company=company,
            departure_time=departure_time,
            arrival_time=arrival_time,
            memo=memo,
            date=date.today().strftime("%Y-%m-%d"),
            timestamp=now_kst()
        )
        db.add(transportation)
        db.commit()
        db.refresh(transportation)
        return transportation

    @staticmethod
    def get_all_transportations(db: Session) -> List[Transportation]:
        """모든 교통수단 기록을 시간순으로 조회합니다."""
        return db.query(Transportation).order_by(Transportation.timestamp.desc()).all()

    @staticmethod
    def get_transportation(db: Session, transportation_id: int) -> Optional[Transportation]:
        """특정 ID의 교통수단 기록을 조회합니다."""
        return db.query(Transportation).filter(Transportation.id == transportation_id).first()

    @staticmethod
    def update_transportation(db: Session, transportation_id: int, category: str = None,
                             departure_time: str = None, arrival_time: str = None,
                             memo: str = None, company: str = None, transportation_date: str = None) -> Optional[Transportation]:
        """교통수단 기록을 수정합니다."""
        transportation = db.query(Transportation).filter(Transportation.id == transportation_id).first()
        if transportation:
            if category is not None:
                transportation.category = category
            if company is not None:
                transportation.company = company
            if departure_time is not None:
                transportation.departure_time = departure_time
            if arrival_time is not None:
                transportation.arrival_time = arrival_time
            if memo is not None:
                transportation.memo = memo
            if transportation_date is not None:
                transportation.date = transportation_date

            db.commit()
            db.refresh(transportation)
            return transportation
        return None

    @staticmethod
    def delete_transportation(db: Session, transportation_id: int) -> bool:
        """교통수단 기록을 삭제합니다."""
        transportation = db.query(Transportation).filter(Transportation.id == transportation_id).first()
        if transportation:
            db.delete(transportation)
            db.commit()
            return True
        return False

    @staticmethod
    def get_transportations_by_date(db: Session, target_date: str) -> List[Transportation]:
        """특정 날짜의 교통수단 기록을 조회합니다."""
        return db.query(Transportation).filter(Transportation.date == target_date).order_by(Transportation.departure_time).all()

    @staticmethod
    def get_transportations_by_category(db: Session, category: str) -> List[Transportation]:
        """특정 카테고리의 교통수단 기록을 조회합니다."""
        return db.query(Transportation).filter(Transportation.category == category).order_by(Transportation.timestamp.desc()).all()

    @staticmethod
    def get_filtered_transportations(
        db: Session,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc"
    ) -> List[Transportation]:
        """필터와 정렬 조건에 따른 교통수단 기록을 조회합니다."""
        query = db.query(Transportation)

        # 필터 적용
        if category:
            query = query.filter(Transportation.category == category)

        if date_from:
            query = query.filter(Transportation.date >= date_from)

        if date_to:
            query = query.filter(Transportation.date <= date_to)

        # 정렬 적용
        if sort_by == "date":
            if sort_order == "asc":
                query = query.order_by(Transportation.date.asc(), Transportation.departure_time.asc())
            else:
                query = query.order_by(Transportation.date.desc(), Transportation.departure_time.desc())
        elif sort_by == "departure_time":
            if sort_order == "asc":
                query = query.order_by(Transportation.departure_time.asc())
            else:
                query = query.order_by(Transportation.departure_time.desc())
        else:
            # 기본 정렬: 최신 등록순
            query = query.order_by(Transportation.timestamp.desc())

        return query.all()

    # 사용자별 메서드
    @staticmethod
    def get_user_transportations(db: Session, user_id: int) -> List[Transportation]:
        """특정 사용자의 모든 교통수단 기록을 조회합니다."""
        return db.query(Transportation).filter(Transportation.user_id == user_id).order_by(Transportation.timestamp.desc()).all()

    @staticmethod
    def get_user_transportation(db: Session, user_id: int, transportation_id: int) -> Optional[Transportation]:
        """특정 사용자의 특정 교통수단 기록을 조회합니다."""
        return db.query(Transportation).filter(
            Transportation.id == transportation_id,
            Transportation.user_id == user_id
        ).first()

    @staticmethod
    def update_user_transportation(db: Session, user_id: int, transportation_id: int,
                                  category: str = None, departure_time: str = None,
                                  arrival_time: str = None, memo: str = None,
                                  company: str = None, transportation_date: str = None) -> Optional[Transportation]:
        """특정 사용자의 교통수단 기록을 수정합니다."""
        transportation = db.query(Transportation).filter(
            Transportation.id == transportation_id,
            Transportation.user_id == user_id
        ).first()
        if transportation:
            if category is not None:
                transportation.category = category
            if company is not None:
                transportation.company = company
            if departure_time is not None:
                transportation.departure_time = departure_time
            if arrival_time is not None:
                transportation.arrival_time = arrival_time
            if memo is not None:
                transportation.memo = memo
            if transportation_date is not None:
                transportation.date = transportation_date

            db.commit()
            db.refresh(transportation)
            return transportation
        return None

    @staticmethod
    def delete_user_transportation(db: Session, user_id: int, transportation_id: int) -> bool:
        """특정 사용자의 교통수단 기록을 삭제합니다."""
        transportation = db.query(Transportation).filter(
            Transportation.id == transportation_id,
            Transportation.user_id == user_id
        ).first()
        if transportation:
            db.delete(transportation)
            db.commit()
            return True
        return False