"""
Claude Agent SDK integration with Context Graph tools.
Provides 9 MCP tools for querying and updating the context graph.
"""

import json
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, create_sdk_mcp_server, tool

from .context_graph_client import context_graph_client
from .gds_client import gds_client
from .vector_client import vector_client

# ============================================
# SYSTEM PROMPT
# ============================================

CONTEXT_GRAPH_SYSTEM_PROMPT = """You are an AI assistant for a financial institution with access to a Context Graph.

The Context Graph stores decision traces - the reasoning, context, and causal relationships behind every significant decision made in the organization. This enables you to:

1. **Find Precedents**: Search for similar past decisions to inform current recommendations
2. **Trace Causality**: Understand how past decisions influenced subsequent outcomes
3. **Record Decisions**: Create new decision traces with full reasoning context
4. **Detect Patterns**: Identify fraud patterns and entity duplicates using graph structure

## Key Concepts

**Event Clock vs State Clock**:
- Traditional systems store the "state clock" - what is true right now
- The Context Graph stores the "event clock" - what happened, when, and with what reasoning

**Decision Traces**:
- Every significant decision is recorded with full reasoning
- Risk factors, confidence scores, and applied policies are captured
- Causal chains show how decisions influenced each other

## Guidelines

When helping users:
1. **Always search for precedents** before making recommendations
2. **Explain your reasoning thoroughly** - this becomes part of the decision trace
3. **Cite specific past decisions** when they inform your recommendation
4. **Flag exceptions or escalations** that may be needed
5. **Consider both structural and semantic similarity** when finding related cases

You have access to tools that leverage both:
- **Semantic similarity** (text embeddings) - for matching by meaning
- **Structural similarity** (FastRP graph embeddings) - for matching by relationship patterns

This combination provides insights that are impossible with traditional databases."""


# ============================================
# MCP TOOLS
# ============================================


@tool(
    "search_customer",
    "Search for customers by name, email, or account number. Returns customer profiles with risk scores and related account counts.",
    {"query": str, "limit": int},
)
async def search_customer(args: dict[str, Any]) -> dict[str, Any]:
    """Search for customers in the context graph."""
    try:
        results = context_graph_client.search_customers(
            query=args["query"], limit=args.get("limit", 10)
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error searching customers: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "get_customer_decisions",
    "Get all decisions made about a specific customer, including approvals, rejections, escalations, and exceptions.",
    {"customer_id": str, "decision_type": str, "limit": int},
)
async def get_customer_decisions(args: dict[str, Any]) -> dict[str, Any]:
    """Get decisions about a customer."""
    try:
        results = context_graph_client.get_customer_decisions(
            customer_id=args["customer_id"],
            decision_type=args.get("decision_type"),
            limit=args.get("limit", 20),
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting decisions: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "find_similar_decisions",
    "Find structurally similar past decisions using FastRP graph embeddings. Returns decisions with similar patterns of entities, relationships, and outcomes.",
    {"decision_id": str, "limit": int},
)
async def find_similar_decisions(args: dict[str, Any]) -> dict[str, Any]:
    """Find similar decisions using FastRP embeddings."""
    try:
        results = gds_client.find_similar_decisions_knn(
            decision_id=args["decision_id"], limit=args.get("limit", 5)
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error finding similar decisions: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "find_precedents",
    "Find precedent decisions that could inform the current decision. Uses both semantic similarity (meaning) and structural similarity (graph patterns).",
    {"scenario": str, "category": str, "limit": int},
)
async def find_precedents(args: dict[str, Any]) -> dict[str, Any]:
    """Find precedent decisions using hybrid search."""
    try:
        results = vector_client.find_precedents_hybrid(
            scenario=args["scenario"], category=args.get("category"), limit=args.get("limit", 5)
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error finding precedents: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "get_causal_chain",
    "Trace the causal chain of a decision - what caused it and what it led to. Useful for understanding decision impact and history.",
    {"decision_id": str, "direction": str, "depth": int},
)
async def get_causal_chain(args: dict[str, Any]) -> dict[str, Any]:
    """Get the causal chain for a decision."""
    try:
        results = context_graph_client.get_causal_chain(
            decision_id=args["decision_id"],
            direction=args.get("direction", "both"),
            depth=args.get("depth", 3),
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting causal chain: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "record_decision",
    "Record a new decision with full reasoning context. Creates a decision trace in the context graph that can be referenced by future decisions.",
    {
        "decision_type": str,
        "category": str,
        "reasoning": str,
        "customer_id": str,
        "account_id": str,
        "risk_factors": list,
        "precedent_ids": list,
        "confidence_score": float,
    },
)
async def record_decision(args: dict[str, Any]) -> dict[str, Any]:
    """Record a new decision in the context graph."""
    try:
        # Generate embedding for the reasoning
        reasoning_embedding = None
        try:
            reasoning_embedding = vector_client.generate_embedding(args["reasoning"])
        except Exception:
            pass  # Continue without embedding if it fails

        decision_id = context_graph_client.record_decision(
            decision_type=args["decision_type"],
            category=args["category"],
            reasoning=args["reasoning"],
            customer_id=args.get("customer_id"),
            account_id=args.get("account_id"),
            risk_factors=args.get("risk_factors", []),
            precedent_ids=args.get("precedent_ids", []),
            confidence_score=args.get("confidence_score", 0.8),
            reasoning_embedding=reasoning_embedding,
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "decision_id": decision_id,
                            "message": f"Decision recorded successfully with ID {decision_id}",
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error recording decision: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "detect_fraud_patterns",
    "Analyze accounts or transactions for potential fraud patterns using graph structure analysis. Uses Node Similarity to compare against known fraud cases.",
    {"account_id": str, "similarity_threshold": float},
)
async def detect_fraud_patterns(args: dict[str, Any]) -> dict[str, Any]:
    """Detect fraud patterns using graph analysis."""
    try:
        results = gds_client.detect_fraud_patterns(
            account_id=args.get("account_id"),
            similarity_threshold=args.get("similarity_threshold", 0.7),
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error detecting fraud patterns: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "get_policy",
    "Get the current policy rules for a specific category. Returns policy details including thresholds and requirements.",
    {"category": str, "policy_name": str},
)
async def get_policy(args: dict[str, Any]) -> dict[str, Any]:
    """Get policy information."""
    try:
        if args.get("policy_name"):
            # Search by name
            policies = context_graph_client.get_policies(category=args.get("category"))
            matching = [
                p for p in policies if args["policy_name"].lower() in p.get("name", "").lower()
            ]
            results = matching[0] if matching else None
        else:
            results = context_graph_client.get_policies(category=args.get("category"))

        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error getting policy: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "execute_cypher",
    "Execute a read-only Cypher query against the context graph for custom analysis. Only SELECT/MATCH queries are allowed.",
    {"cypher": str},
)
async def execute_cypher(args: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only Cypher query."""
    try:
        results = context_graph_client.execute_cypher(cypher=args["cypher"])
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Query not allowed: {str(e)}"}],
            "is_error": True,
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error executing query: {str(e)}"}],
            "is_error": True,
        }


# ============================================
# MCP SERVER CREATION
# ============================================


def create_context_graph_server():
    """Create the MCP server with all context graph tools."""
    return create_sdk_mcp_server(
        name="context-graph",
        version="1.0.0",
        tools=[
            search_customer,
            get_customer_decisions,
            find_similar_decisions,
            find_precedents,
            get_causal_chain,
            record_decision,
            detect_fraud_patterns,
            get_policy,
            execute_cypher,
        ],
    )


def get_agent_options() -> ClaudeAgentOptions:
    """Get the agent options with context graph server configured."""
    context_graph_server = create_context_graph_server()

    return ClaudeAgentOptions(
        system_prompt=CONTEXT_GRAPH_SYSTEM_PROMPT,
        mcp_servers={"graph": context_graph_server},
        allowed_tools=[
            "mcp__graph__search_customer",
            "mcp__graph__get_customer_decisions",
            "mcp__graph__find_similar_decisions",
            "mcp__graph__find_precedents",
            "mcp__graph__get_causal_chain",
            "mcp__graph__record_decision",
            "mcp__graph__detect_fraud_patterns",
            "mcp__graph__get_policy",
            "mcp__graph__execute_cypher",
        ],
    )


# ============================================
# AGENT SESSION MANAGEMENT
# ============================================


class ContextGraphAgent:
    """Wrapper for managing Claude Agent SDK sessions."""

    def __init__(self):
        self.options = get_agent_options()
        self.client: ClaudeSDKClient | None = None

    async def __aenter__(self):
        self.client = ClaudeSDKClient(options=self.options)
        await self.client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.disconnect()

    async def query(self, message: str) -> dict[str, Any]:
        """Send a query to the agent and get the response."""
        if not self.client:
            raise RuntimeError("Agent not connected. Use 'async with' context manager.")

        await self.client.query(message)

        response_text = ""
        tool_calls = []
        decisions_made = []

        async for msg in self.client.receive_response():
            # Process different message types
            if hasattr(msg, "content"):
                for block in msg.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                    elif hasattr(block, "name"):
                        # Tool use block
                        tool_calls.append(
                            {
                                "name": block.name,
                                "input": block.input if hasattr(block, "input") else {},
                            }
                        )
                        # Track decisions made
                        if block.name == "mcp__graph__record_decision":
                            # Will be populated when we get the result
                            pass

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "decisions_made": decisions_made,
        }
