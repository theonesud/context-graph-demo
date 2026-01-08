"""
Pydantic models for decision trace nodes (Event Clock pattern).
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

DecisionType = Literal["approval", "rejection", "escalation", "exception", "override", "review"]
DecisionCategory = Literal[
    "credit", "fraud", "compliance", "trading", "support", "account_management"
]
DecisionStatus = Literal["pending", "approved", "rejected", "escalated", "completed"]


class Decision(BaseModel):
    """Core decision event with full context - the heart of the context graph."""

    id: str
    decision_type: DecisionType
    category: DecisionCategory
    status: DecisionStatus = "pending"

    # THE EVENT CLOCK - when decision was made
    decision_timestamp: datetime

    # The reasoning/context - the decision trace
    reasoning: str
    reasoning_summary: Optional[str] = None
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)

    # Context snapshot at decision time
    context_snapshot: Optional[str] = None  # JSON
    risk_factors: list[str] = Field(default_factory=list)

    # Metadata
    source_system: Optional[str] = None
    session_id: Optional[str] = None

    # Embeddings
    fastrp_embedding: Optional[list[float]] = None  # 128 dims, structural
    reasoning_embedding: Optional[list[float]] = None  # 1536 dims, semantic

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DecisionContext(BaseModel):
    """Snapshot of state at decision time."""

    id: str
    decision_id: str
    context_type: str  # 'customer_profile', 'account_state', 'market_conditions'
    state_snapshot: str  # JSON
    timestamp: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Precedent(BaseModel):
    """Historical decisions used as reference."""

    id: str
    description: str
    outcome: str  # 'successful', 'failed', 'revised'
    lessons_learned: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Policy(BaseModel):
    """Rules and policies governing decisions."""

    id: str
    name: str
    description: str
    category: DecisionCategory
    version: str = "1.0"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    threshold_rules: Optional[str] = None  # JSON
    description_embedding: Optional[list[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Exception(BaseModel):
    """Documented exceptions to normal process."""

    id: str
    exception_type: str  # 'policy_override', 'limit_increase', 'manual_approval'
    justification: str
    risk_acceptance: Optional[str] = None
    expiry_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Escalation(BaseModel):
    """Escalation events."""

    id: str
    escalation_level: int = Field(ge=1, le=3)
    reason: str
    urgency: str = "medium"  # 'low', 'medium', 'high', 'critical'
    resolution: Optional[str] = None
    resolution_time_hours: Optional[float] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CausalChain(BaseModel):
    """Causal chain of decisions - causes and effects."""

    decision_id: str
    causes: list[Decision] = Field(default_factory=list)
    effects: list[Decision] = Field(default_factory=list)
    depth: int = 1


class SimilarDecision(BaseModel):
    """A decision with similarity score."""

    decision: Decision
    similarity_score: float = Field(ge=0.0, le=1.0)
    similarity_type: str = "structural"  # 'structural', 'semantic', 'combined'
