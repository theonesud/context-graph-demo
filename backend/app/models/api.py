"""
Pydantic models for API requests and responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request to send a message to the AI agent."""

    message: str
    session_id: Optional[str] = None


class ToolCall(BaseModel):
    """Record of a tool call made by the agent."""

    name: str
    arguments: dict[str, Any]
    output: Optional[Any] = None


class ChatResponse(BaseModel):
    """Response from the AI agent."""

    response: str
    session_id: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)  # Decision IDs


class DecisionRequest(BaseModel):
    """Request to record a new decision."""

    decision_type: str
    category: str
    reasoning: str
    customer_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    risk_factors: list[str] = Field(default_factory=list)
    precedent_ids: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)


class GraphNode(BaseModel):
    """A node in the graph for visualization."""

    id: str
    labels: list[str]
    properties: dict[str, Any]


class GraphRelationship(BaseModel):
    """A relationship in the graph for visualization."""

    id: str
    type: str
    start_node_id: str
    end_node_id: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """Graph data for NVL visualization."""

    nodes: list[GraphNode]
    relationships: list[GraphRelationship]


class CustomerSearchResult(BaseModel):
    """Result from customer search."""

    id: str
    name: str
    email: Optional[str] = None
    risk_score: float
    account_count: int = 0
    decision_count: int = 0


class FraudPattern(BaseModel):
    """Detected fraud pattern."""

    account_id: str
    account_number: str
    similarity_to_fraud: float
    risk_indicators: list[str] = Field(default_factory=list)
    similar_fraud_cases: list[str] = Field(default_factory=list)


class EntityMatch(BaseModel):
    """Potential duplicate entity match."""

    entity1_id: str
    entity1_name: str
    entity2_id: str
    entity2_name: str
    similarity_score: float
    match_reasons: list[str] = Field(default_factory=list)


class CommunityInfo(BaseModel):
    """Information about a decision community."""

    community_id: int
    decision_count: int
    decision_types: list[str]
    categories: list[str]
    top_decisions: list[str] = Field(default_factory=list)
