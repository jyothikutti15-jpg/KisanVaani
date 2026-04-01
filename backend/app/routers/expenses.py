from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.farmer import FarmerExpense

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


class ExpenseCreate(BaseModel):
    farmer_id: int
    category: str
    description: str
    amount: float
    date: Optional[str] = None
    crop: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    farmer_id: int
    category: str
    description: str
    amount: float
    date: Optional[str] = None
    crop: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class ExpenseSummary(BaseModel):
    total_spent: float
    by_category: dict[str, float]
    by_crop: dict[str, float]
    expense_count: int


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    expense = FarmerExpense(
        farmer_id=data.farmer_id,
        category=data.category,
        description=data.description,
        amount=data.amount,
        date=data.date,
        crop=data.crop,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseResponse(
        id=expense.id, farmer_id=expense.farmer_id, category=expense.category,
        description=expense.description, amount=expense.amount,
        date=expense.date, crop=expense.crop, created_at=str(expense.created_at),
    )


@router.get("/{farmer_id}", response_model=list[ExpenseResponse])
def get_expenses(farmer_id: int, db: Session = Depends(get_db)):
    expenses = db.query(FarmerExpense).filter(
        FarmerExpense.farmer_id == farmer_id
    ).order_by(FarmerExpense.created_at.desc()).limit(100).all()
    return [
        ExpenseResponse(
            id=e.id, farmer_id=e.farmer_id, category=e.category,
            description=e.description, amount=e.amount,
            date=e.date, crop=e.crop, created_at=str(e.created_at),
        )
        for e in expenses
    ]


@router.get("/{farmer_id}/summary", response_model=ExpenseSummary)
def get_expense_summary(farmer_id: int, db: Session = Depends(get_db)):
    expenses = db.query(FarmerExpense).filter(FarmerExpense.farmer_id == farmer_id).all()

    total = sum(e.amount for e in expenses)
    by_category: dict[str, float] = {}
    by_crop: dict[str, float] = {}

    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount
        if e.crop:
            by_crop[e.crop] = by_crop.get(e.crop, 0) + e.amount

    return ExpenseSummary(
        total_spent=total,
        by_category=by_category,
        by_crop=by_crop,
        expense_count=len(expenses),
    )
