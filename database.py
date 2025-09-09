from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Expense
from datetime import datetime, date
from typing import List, Optional

class ExpenseService:
    """Service class for expense database operations."""
    
    @staticmethod
    def create_expense(db: Session, amount: float, category: str, description: str = "") -> Expense:
        """Create a new expense record."""
        expense = Expense(
            amount=amount,
            category=category,
            description=description,
            date=date.today().strftime("%Y-%m-%d"),
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
    def update_expense(db: Session, expense_id: int, amount: float = None, 
                      category: str = None, description: str = None, 
                      expense_date: str = None) -> Optional[Expense]:
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
            
            db.commit()
            db.refresh(expense)
            return expense
        return None