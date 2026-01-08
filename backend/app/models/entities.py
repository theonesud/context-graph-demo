"""
Pydantic models for core entities (identity-resolved).
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    """Unified customer/employee identity."""

    id: str
    canonical_id: Optional[str] = None
    name: str
    normalized_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_systems: list[str] = Field(default_factory=list)
    fastrp_embedding: Optional[list[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Account(BaseModel):
    """Bank accounts, trading accounts."""

    id: str
    account_number: str
    account_type: str  # 'checking', 'savings', 'trading', 'margin'
    status: str = "active"  # 'active', 'frozen', 'closed'
    balance: float = 0.0
    currency: str = "USD"
    risk_tier: str = "low"  # 'low', 'medium', 'high', 'critical'
    opened_date: Optional[date] = None
    source_system: Optional[str] = None
    fastrp_embedding: Optional[list[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Transaction(BaseModel):
    """Financial transactions."""

    id: str
    transaction_id: Optional[str] = None
    type: str  # 'deposit', 'withdrawal', 'transfer', 'trade'
    amount: float
    currency: str = "USD"
    timestamp: datetime
    status: str = "completed"  # 'pending', 'completed', 'flagged', 'reversed'
    channel: Optional[str] = None  # 'online', 'branch', 'atm', 'wire'
    description: Optional[str] = None
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_system: Optional[str] = None
    fastrp_embedding: Optional[list[float]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Organization(BaseModel):
    """Companies, counterparties."""

    id: str
    name: str
    normalized_name: Optional[str] = None
    type: Optional[str] = None  # 'corporation', 'bank', 'broker', 'vendor'
    industry: Optional[str] = None
    country: Optional[str] = None
    risk_rating: Optional[str] = None
    sanctions_status: str = "clear"  # 'clear', 'watchlist', 'blocked'
    source_systems: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Employee(BaseModel):
    """Staff members."""

    id: str
    employee_id: Optional[str] = None
    name: str
    department: Optional[str] = None  # 'Trading', 'Compliance', 'Risk', 'Support'
    role: Optional[str] = None  # 'Analyst', 'Manager', 'Director', 'VP'
    authorization_level: int = Field(default=1, ge=1, le=5)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
