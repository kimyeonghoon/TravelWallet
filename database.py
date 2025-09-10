from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Expense
from datetime import datetime, date
from typing import List, Optional

class ExpenseService:
    """Service class for expense database operations."""
    
    @staticmethod
    def create_expense(db: Session, user_id: int, amount: float, category: str, description: str = "", payment_method: str = "현금") -> Expense:
        """Create a new expense record for a user."""
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            description=description,
            date=date.today().strftime("%Y-%m-%d"),
            payment_method=payment_method,
            timestamp=datetime.utcnow()
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
    
    @staticmethod
    def get_all_expenses(db: Session) -> List[Expense]:
        """Get all expenses ordered by timestamp descending."""
        return db.query(Expense).order_by(Expense.timestamp.desc()).all()
    
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
        sort_order: Optional[str] = "desc"
    ) -> List[Expense]:
        """Get expenses with optional filters and sorting."""
        query = db.query(Expense)
        
        # Apply filters
        if category:
            query = query.filter(Expense.category == category)
        
        if payment_method:
            query = query.filter(Expense.payment_method == payment_method)
        
        if date_from:
            query = query.filter(Expense.date >= date_from)
        
        if date_to:
            query = query.filter(Expense.date <= date_to)
        
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
    def update_expense(db: Session, expense_id: int, amount: float = None, 
                      category: str = None, description: str = None, 
                      expense_date: str = None, expense_time: str = None,
                      payment_method: str = None) -> Optional[Expense]:
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
                          payment_method: str = None) -> Optional[Expense]:
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