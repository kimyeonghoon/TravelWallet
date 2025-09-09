from fastapi import FastAPI, Request, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from models import create_tables, get_db, User
from database import ExpenseService
from auth import AuthService

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
    payment_method: str = "현금"

class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: str
    date: str
    payment_method: str
    timestamp: str

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    payment_method: Optional[str] = None

class SummaryResponse(BaseModel):
    total_expense: float
    today_expense: float

# Authentication models
class LoginRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    message: str
    email: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

# Security
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_token: str = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token."""
    token = None
    
    if credentials:
        token = credentials.credentials
    elif session_token:
        token = session_token
    
    if not token:
        return None
    
    payload = AuthService.verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None

async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require authentication for protected routes."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: User = Depends(get_current_user)):
    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Japan Travel Expense API is running"}

# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def request_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Request magic link login email."""
    try:
        # Create or get user
        user = AuthService.create_user(db, login_data.email)
        
        # Create login token
        login_token = AuthService.create_login_token(db, user.id)
        
        # Generate magic link
        magic_link = f"http://localhost:8000/auth/verify/{login_token.token}"
        
        # Send email
        email_sent = AuthService.send_magic_link_email(login_data.email, magic_link)
        
        if not email_sent:
            print(f"Magic link for {login_data.email}: {magic_link}")
        
        return LoginResponse(
            message="로그인 링크가 이메일로 전송되었습니다. 이메일을 확인해주세요.",
            email=login_data.email
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send login email: {str(e)}")

@app.get("/auth/verify/{token}")
async def verify_login(token: str, db: Session = Depends(get_db)):
    """Verify magic link and login user."""
    user = AuthService.validate_login_token(db, token)
    
    if not user:
        return RedirectResponse(
            url="/login?error=invalid_token",
            status_code=302
        )
    
    # Create JWT access token
    access_token = AuthService.create_access_token({"user_id": user.id})
    
    # Redirect to main app with token in cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=900,  # 15 minutes
        secure=False  # Set to True in production with HTTPS
    )
    
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/auth/logout")
async def logout():
    """Logout user by clearing session cookie."""
    response = JSONResponse({"message": "Successfully logged out"})
    response.delete_cookie("session_token")
    return response

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active
    )

@app.post("/api/expenses", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Create a new expense."""
    try:
        new_expense = ExpenseService.create_expense(
            db=db, 
            user_id=current_user.id,
            amount=expense.amount, 
            category=expense.category, 
            description=expense.description,
            payment_method=expense.payment_method
        )
        return ExpenseResponse(**new_expense.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses", response_model=List[ExpenseResponse])
async def get_expenses(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Get all expenses for current user."""
    expenses = ExpenseService.get_user_expenses(db, current_user.id)
    return [ExpenseResponse(**expense.to_dict()) for expense in expenses]

@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: int, expense_update: ExpenseUpdate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Update an expense."""
    updated_expense = ExpenseService.update_user_expense(
        db=db,
        user_id=current_user.id,
        expense_id=expense_id,
        amount=expense_update.amount,
        category=expense_update.category,
        description=expense_update.description,
        expense_date=expense_update.date,
        expense_time=expense_update.time,
        payment_method=expense_update.payment_method
    )
    if not updated_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ExpenseResponse(**updated_expense.to_dict())

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Delete an expense."""
    success = ExpenseService.delete_user_expense(db, current_user.id, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

@app.get("/api/summary", response_model=SummaryResponse)
async def get_summary(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Get expense summary for current user."""
    total_expense = ExpenseService.get_user_total_expenses(db, current_user.id)
    today_expense = ExpenseService.get_user_today_expenses_total(db, current_user.id)
    
    return SummaryResponse(
        total_expense=total_expense,
        today_expense=today_expense
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)