"""
FastAPI application for the Context Graph demo.
Provides REST API endpoints for the frontend and agent interactions.
"""

import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agent import ContextGraphAgent
from .config import config
from .context_graph_client import context_graph_client
from .gds_client import gds_client
from .models import (
    ChatRequest,
    ChatResponse,
    DecisionRequest,
    GraphData,
    GraphNode,
    GraphRelationship,
)
from .vector_client import vector_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Context Graph API...")
    if context_graph_client.verify_connectivity():
        print("Connected to Neo4j successfully!")
    else:
        print("Warning: Could not connect to Neo4j")
    yield
    # Shutdown
    print("Shutting down Context Graph API...")
    context_graph_client.close()
    gds_client.close()
    vector_client.close()


app = FastAPI(
    title="Context Graph API",
    description="Decision traces for AI agents using Neo4j",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HEALTH CHECK
# ============================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    neo4j_connected = context_graph_client.verify_connectivity()
    return {
        "status": "healthy" if neo4j_connected else "degraded",
        "neo4j_connected": neo4j_connected,
    }


# ============================================
# CHAT / AGENT ENDPOINTS
# ============================================


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the Claude agent.
    Agent has access to context graph tools.
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        async with ContextGraphAgent() as agent:
            result = await agent.query(request.message)

            return ChatResponse(
                response=result["response"],
                session_id=session_id,
                tool_calls=result.get("tool_calls", []),
                decisions_made=result.get("decisions_made", []),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CUSTOMER ENDPOINTS
# ============================================


@app.get("/api/customers/search")
async def search_customers(query: str, limit: int = 10):
    """Search for customers by name, email, or account number."""
    try:
        results = context_graph_client.search_customers(query, limit)
        return {"customers": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get a customer by ID with related entities."""
    customer = context_graph_client.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/api/customers/{customer_id}/decisions")
async def get_customer_decisions(
    customer_id: str,
    decision_type: Optional[str] = None,
    limit: int = 20,
):
    """Get all decisions about a customer."""
    try:
        decisions = context_graph_client.get_customer_decisions(customer_id, decision_type, limit)
        return {"decisions": decisions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DECISION ENDPOINTS
# ============================================


@app.get("/api/decisions/{decision_id}")
async def get_decision(decision_id: str):
    """Get a decision by ID with full context."""
    decision = context_graph_client.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@app.post("/api/decisions")
async def create_decision(request: DecisionRequest):
    """Record a new decision."""
    try:
        # Generate reasoning embedding
        reasoning_embedding = None
        try:
            reasoning_embedding = vector_client.generate_embedding(request.reasoning)
        except Exception:
            pass

        decision_id = context_graph_client.record_decision(
            decision_type=request.decision_type,
            category=request.category,
            reasoning=request.reasoning,
            customer_id=request.customer_id,
            account_id=request.account_id,
            transaction_id=request.transaction_id,
            risk_factors=request.risk_factors,
            precedent_ids=request.precedent_ids,
            confidence_score=request.confidence_score,
            reasoning_embedding=reasoning_embedding,
        )
        return {"decision_id": decision_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decisions/{decision_id}/similar")
async def find_similar_decisions(decision_id: str, limit: int = 5):
    """Find structurally similar decisions using FastRP embeddings."""
    try:
        similar = gds_client.find_similar_decisions_knn(decision_id, limit)
        return {"similar_decisions": similar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decisions/{decision_id}/causal-chain")
async def get_causal_chain(decision_id: str, depth: int = 3):
    """Get the causal chain for a decision."""
    try:
        chain = context_graph_client.get_causal_chain(decision_id, "both", depth)
        return chain
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decisions/search/precedents")
async def find_precedents(scenario: str, category: Optional[str] = None, limit: int = 5):
    """Find precedent decisions using hybrid search."""
    try:
        precedents = vector_client.find_precedents_hybrid(scenario, category, limit=limit)
        return {"precedents": precedents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# POLICY ENDPOINTS
# ============================================


@app.get("/api/policies")
async def list_policies(category: Optional[str] = None):
    """List all policies, optionally filtered by category."""
    try:
        policies = context_graph_client.get_policies(category)
        return {"policies": policies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a policy by ID."""
    policy = context_graph_client.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


# ============================================
# GRAPH VISUALIZATION ENDPOINTS
# ============================================


@app.get("/api/graph", response_model=GraphData)
async def get_graph(
    center_node_id: Optional[str] = None,
    center_node_type: Optional[str] = None,
    depth: int = 2,
    include_decisions: bool = True,
    limit: int = 100,
):
    """Get graph data for NVL visualization."""
    try:
        graph = context_graph_client.get_graph_data(
            center_node_id=center_node_id,
            center_node_type=center_node_type,
            depth=depth,
            include_decisions=include_decisions,
            limit=limit,
        )
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/statistics")
async def get_statistics():
    """Get graph statistics."""
    try:
        stats = context_graph_client.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GDS / ANALYTICS ENDPOINTS
# ============================================


@app.post("/api/analytics/fastrp")
async def run_fastrp_embeddings():
    """Generate FastRP embeddings for all nodes."""
    try:
        # Create projection
        projection = gds_client.create_decision_graph_projection()

        # Generate embeddings
        result = gds_client.generate_fastrp_embeddings()

        # Write back to database
        write_result = gds_client.write_fastrp_embeddings()

        return {
            "projection": projection,
            "embeddings": result,
            "written": write_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/communities")
async def get_decision_communities():
    """Get detected decision communities."""
    try:
        communities = gds_client.detect_decision_communities()
        return {"communities": communities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/influence")
async def get_influence_scores():
    """Get influence scores for decisions using PageRank."""
    try:
        scores = gds_client.calculate_influence_scores()
        return {"influence_scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/fraud-patterns")
async def detect_fraud_patterns(
    account_id: Optional[str] = None,
    similarity_threshold: float = 0.7,
):
    """Detect potential fraud patterns."""
    try:
        patterns = gds_client.detect_fraud_patterns(account_id, similarity_threshold)
        return {"fraud_patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/entity-resolution")
async def find_entity_matches(similarity_threshold: float = 0.7):
    """Find potential duplicate entities."""
    try:
        matches = gds_client.find_potential_duplicates(similarity_threshold)
        return {"entity_matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/projections")
async def list_graph_projections():
    """List all GDS graph projections."""
    try:
        projections = gds_client.list_graph_projections()
        return {"projections": projections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# VECTOR SEARCH ENDPOINTS
# ============================================


@app.get("/api/search/decisions")
async def search_decisions_semantic(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
):
    """Search decisions by semantic similarity."""
    try:
        results = vector_client.search_decisions_semantic(query, limit, category)
        return {"decisions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/policies")
async def search_policies_semantic(query: str, limit: int = 5):
    """Search policies by semantic similarity."""
    try:
        results = vector_client.search_policies_semantic(query, limit)
        return {"policies": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/embeddings/batch-update")
async def batch_update_embeddings(limit: int = 100):
    """Generate embeddings for decisions that don't have them."""
    try:
        count = vector_client.batch_update_decision_embeddings(limit)
        return {"updated_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.host, port=config.port)
