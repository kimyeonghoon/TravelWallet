from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from models import create_tables, get_db
from database import ExpenseService

# Create database tables
create_tables()

app = FastAPI(title="Japan Travel Expense Tracker")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models for API
class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str = ""

class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: str
    date: str
    timestamp: str

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None

class SummaryResponse(BaseModel):
    total_expense: float
    today_expense: float

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Japan Travel Expense API is running"}

@app.post("/api/expenses", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense."""
    try:
        new_expense = ExpenseService.create_expense(
            db=db, 
            amount=expense.amount, 
            category=expense.category, 
            description=expense.description
        )
        return ExpenseResponse(**new_expense.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses", response_model=List[ExpenseResponse])
async def get_expenses(db: Session = Depends(get_db)):
    """Get all expenses."""
    expenses = ExpenseService.get_all_expenses(db)
    return [ExpenseResponse(**expense.to_dict()) for expense in expenses]

@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: int, expense_update: ExpenseUpdate, db: Session = Depends(get_db)):
    """Update an expense."""
    updated_expense = ExpenseService.update_expense(
        db=db,
        expense_id=expense_id,
        amount=expense_update.amount,
        category=expense_update.category,
        description=expense_update.description,
        expense_date=expense_update.date
    )
    if not updated_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ExpenseResponse(**updated_expense.to_dict())

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete an expense."""
    success = ExpenseService.delete_expense(db, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

@app.get("/api/summary", response_model=SummaryResponse)
async def get_summary(db: Session = Depends(get_db)):
    """Get expense summary."""
    total_expense = ExpenseService.get_total_expenses(db)
    today_expense = ExpenseService.get_today_expenses_total(db)
    
    return SummaryResponse(
        total_expense=total_expense,
        today_expense=today_expense
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)