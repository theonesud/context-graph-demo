"""
Gemini Agent integration with Context Graph tools.
Provides tools for querying and updating the context graph.
"""

import json
import logging
from typing import Any, List, Optional, Dict
from google import genai
from google.genai import types

from .context_graph_client import context_graph_client
from .gds_client import gds_client
from .vector_client import vector_client
from .config import config

logger = logging.getLogger(__name__)

def slim_properties(props: dict) -> dict:
    """Remove large properties to reduce response size."""
    slim = {}
    for key, value in props.items():
        # Skip embedding vectors
        if key in ("fastrp_embedding", "reasoning_embedding", "embedding"):
            continue
        # Truncate long strings
        if isinstance(value, str) and len(value) > 200:
            slim[key] = value[:200] + "..."
        # Limit list sizes
        elif isinstance(value, list) and len(value) > 10:
            slim[key] = value[:10]
        else:
            slim[key] = value
    return slim

def get_graph_data_for_entity(entity_id: str, depth: int = 2, limit: int = 30) -> dict:
    """Get graph visualization data centered on an entity."""
    try:
        graph_data = context_graph_client.get_graph_data(
            center_node_id=entity_id, depth=depth, limit=limit
        )
        # Build nodes list first
        nodes = [
            {
                "id": node.id,
                "labels": node.labels,
                "properties": slim_properties(node.properties),
            }
            for node in graph_data.nodes
        ]

        # Create set of node IDs for filtering relationships
        node_ids = {node["id"] for node in nodes}

        # Only include relationships where both nodes exist
        relationships = [
            {
                "id": rel.id,
                "type": rel.type,
                "startNodeId": rel.start_node_id,
                "endNodeId": rel.end_node_id,
                "properties": slim_properties(rel.properties),
            }
            for rel in graph_data.relationships
            if rel.start_node_id in node_ids and rel.end_node_id in node_ids
        ]

        return {
            "nodes": nodes,
            "relationships": relationships,
        }
    except Exception as e:
        logger.error(f"Error getting graph data for entity {entity_id}: {e}")
        return {"nodes": [], "relationships": []}

def merge_graph_data(graphs: list[dict], max_nodes: int = 50, max_rels: int = 75) -> dict:
    """Merge multiple graph data objects, removing duplicates and limiting size."""
    all_nodes = {}
    all_relationships = {}

    for graph in graphs:
        if not graph:
            continue
        for node in graph.get("nodes", []):
            if len(all_nodes) < max_nodes:
                all_nodes[node["id"]] = node
        for rel in graph.get("relationships", []):
            # Only include relationships where both nodes are in the graph
            if rel.get("startNodeId") in all_nodes and rel.get("endNodeId") in all_nodes:
                if len(all_relationships) < max_rels:
                    all_relationships[rel["id"]] = rel

    return {
        "nodes": list(all_nodes.values()),
        "relationships": list(all_relationships.values()),
    }

# ============================================
# TOOLS
# ============================================

def search_customer(query: str, limit: int = 10) -> dict:
    """
    Search for customers by name, email, or account number.
    Returns customer profiles with risk scores and related account counts.

    Args:
        query: Search string (name, email, or account number)
        limit: Maximum number of results to return
    """
    try:
        results = context_graph_client.search_customers(query=query, limit=limit)
        # Include graph data for top customers (1 hop from each)
        graphs = []
        for customer in results[:3]:
            customer_id = customer.get("id")
            if customer_id:
                customer_graph = get_graph_data_for_entity(customer_id, depth=1)
                graphs.append(customer_graph)

        graph_data = merge_graph_data(graphs) if graphs else {"nodes": [], "relationships": []}

        return {
            "customers": results,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        return {"error": str(e)}

def get_customer_decisions(customer_id: str, decision_type: Optional[str] = None, limit: int = 20) -> dict:
    """
    Get all decisions made about a specific customer, including approvals, rejections, escalations, and exceptions.

    Args:
        customer_id: The ID of the customer
        decision_type: Optional filter by decision type (e.g., 'Approval', 'Rejection')
        limit: Maximum number of decisions to return
    """
    try:
        results = context_graph_client.get_customer_decisions(
            customer_id=customer_id,
            decision_type=decision_type,
            limit=limit,
        )
        graph_data = get_graph_data_for_entity(customer_id, depth=2)

        return {
            "decisions": results,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        return {"error": str(e)}

def find_similar_decisions(decision_id: str, limit: int = 5) -> dict:
    """
    Find structurally similar past decisions using FastRP graph embeddings.
    Returns decisions with similar patterns of entities, relationships, and outcomes.

    Args:
        decision_id: The ID of the reference decision
        limit: Maximum number of similar decisions to return
    """
    try:
        results = gds_client.find_similar_decisions_knn(decision_id=decision_id, limit=limit)
        graph_data = get_graph_data_for_entity(decision_id, depth=2)

        return {
            "similar_decisions": results,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error finding similar decisions: {e}")
        return {"error": str(e)}

def find_precedents(scenario: str, category: Optional[str] = None, limit: int = 5) -> dict:
    """
    Find precedent decisions that could inform the current decision.
    Uses both semantic similarity (meaning) and structural similarity (graph patterns).

    Args:
        scenario: Description of the current situation to find precedents for
        category: Optional policy category to filter by
        limit: Maximum number of precedents to return
    """
    try:
        results = vector_client.find_precedents_hybrid(scenario=scenario, category=category, limit=limit)
        graph_data = None
        if results and len(results) > 0:
            first_id = results[0].get("id") if isinstance(results[0], dict) else None
            if first_id:
                graph_data = get_graph_data_for_entity(first_id, depth=2)

        return {
            "precedents": results,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error finding precedents: {e}")
        return {"error": str(e)}

def get_causal_chain(decision_id: str, direction: str = "both", depth: int = 3) -> dict:
    """
    Trace the causal chain of a decision - what caused it and what it led to.
    Useful for understanding decision impact and history.

    Args:
        decision_id: The ID of the decision to trace
        direction: Direction to trace: 'upstream', 'downstream', or 'both'
        depth: Maximum depth of the causal chain
    """
    try:
        results = context_graph_client.get_causal_chain(
            decision_id=decision_id,
            direction=direction,
            depth=depth,
        )
        graph_data = get_graph_data_for_entity(decision_id, depth=3)

        return {
            "causal_chain": results,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error getting causal chain: {e}")
        return {"error": str(e)}

def record_decision(
    decision_type: str,
    category: str,
    reasoning: str,
    customer_id: str,
    account_id: Optional[str] = None,
    risk_factors: Optional[List[str]] = None,
    precedent_ids: Optional[List[str]] = None,
    confidence_score: float = 0.8,
) -> dict:
    """
    Record a new decision with full reasoning context.
    Creates a decision trace in the context graph that can be referenced by future decisions.

    Args:
        decision_type: Type of decision (e.g., 'Credit Approval', 'Fraud Investigation')
        category: Policy category (e.g., 'Credit', 'Onboarding', 'Fraud')
        reasoning: Detailed explanation of the decision logic
        customer_id: ID of the customer the decision relates to
        account_id: Optional ID of the account the decision relates to
        risk_factors: List of risk factor strings considered
        precedent_ids: List of IDs of past decisions that informed this one
        confidence_score: Score from 0.0 to 1.0 representing confidence in the decision
    """
    try:
        reasoning_embedding = None
        try:
            reasoning_embedding = vector_client.generate_embedding(reasoning)
        except Exception:
            pass

        decision_id = context_graph_client.record_decision(
            decision_type=decision_type,
            category=category,
            reasoning=reasoning,
            customer_id=customer_id,
            account_id=account_id,
            risk_factors=risk_factors or [],
            precedent_ids=precedent_ids or [],
            confidence_score=confidence_score,
            reasoning_embedding=reasoning_embedding,
        )

        return {
            "success": True,
            "decision_id": decision_id,
            "message": f"Decision recorded successfully with ID {decision_id}",
        }
    except Exception as e:
        logger.error(f"Error recording decision: {e}")
        return {"error": str(e)}

def detect_fraud_patterns(account_id: Optional[str] = None, similarity_threshold: float = 0.7) -> dict:
    """
    Analyze accounts or transactions for potential fraud patterns using graph structure analysis.
    Uses Node Similarity to compare against known fraud cases.

    Args:
        account_id: Optional specific account to analyze. If omitted, analyzes all active accounts.
        similarity_threshold: Threshold for reporting similar patterns (0.0 to 1.0)
    """
    try:
        results = gds_client.detect_fraud_patterns(
            account_id=account_id,
            similarity_threshold=similarity_threshold,
        )
        return results
    except Exception as e:
        logger.error(f"Error detecting fraud patterns: {e}")
        return {"error": str(e)}

def find_decision_community(decision_id: str, limit: int = 10) -> dict:
    """
    Find decisions in the same community using Louvain community detection.
    Returns decisions related through causal chains and precedents.

    Args:
        decision_id: The ID of the decision to find the community for
        limit: Maximum number of related decisions to return
    """
    try:
        with gds_client.driver.session(database=gds_client.database) as session:
            result = session.run(
                """
                MATCH (source:Decision {id: $decision_id})
                MATCH (other:Decision)
                WHERE other.community_id = source.community_id AND other.id <> source.id
                RETURN other.id AS id,
                       other.decision_type AS decision_type,
                       other.category AS category,
                       other.reasoning_summary AS reasoning_summary,
                       other.decision_timestamp AS decision_timestamp,
                       other.community_id AS community_id
                ORDER BY other.decision_timestamp DESC
                LIMIT $limit
                """,
                {"decision_id": decision_id, "limit": limit},
            )
            community_decisions = [dict(record) for record in result]

        graph_data = get_graph_data_for_entity(decision_id, depth=2)

        return {
            "community_decisions": community_decisions,
            "graph_data": graph_data,
        }
    except Exception as e:
        logger.error(f"Error finding community: {e}")
        return {"error": str(e)}

def get_policy(category: Optional[str] = None, policy_name: Optional[str] = None) -> dict:
    """
    Get current policy rules. Returns details including thresholds and requirements.

    Args:
        category: Policy category to filter by (e.g., 'Credit', 'Fraud')
        policy_name: Search for a specific policy by name
    """
    try:
        policies = context_graph_client.get_policies(category=category)

        if policy_name:
            stop_words = {"the", "a", "an", "for", "and", "or", "of", "in", "to", "with"}
            search_words = [
                word.lower()
                for word in policy_name.split()
                if word.lower() not in stop_words and len(word) > 2
            ]

            scored_policies = []
            for policy in policies:
                policy_name_lower = policy.get("name", "").lower()
                matches = sum(1 for word in search_words if word in policy_name_lower)
                if matches > 0:
                    scored_policies.append({"policy": policy, "relevance_score": matches})

            scored_policies.sort(key=lambda x: x["relevance_score"], reverse=True)

            if scored_policies:
                return {
                    "matching_policies": [
                        {**sp["policy"], "relevance_score": sp["relevance_score"]}
                        for sp in scored_policies
                    ],
                    "total_matches": len(scored_policies),
                }
            else:
                return {
                    "matching_policies": [],
                    "all_policies_in_category": policies,
                    "note": f"No policies matched '{policy_name}'. Showing all in category.",
                }

        return {"policies": policies}
    except Exception as e:
        logger.error(f"Error getting policy: {e}")
        return {"error": str(e)}

def execute_cypher(cypher: str) -> dict:
    """
    Execute a read-only Cypher query against the context graph for custom analysis.
    Only SELECT/MATCH queries are allowed.

    Args:
        cypher: The Cypher query string
    """
    try:
        results = context_graph_client.execute_cypher(cypher=cypher)
        return {"results": results}
    except ValueError as e:
        return {"error": f"Query not allowed: {str(e)}"}
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"error": str(e)}

def get_schema() -> dict:
    """
    Get the graph database schema including node labels, relationship types, and property keys.
    """
    try:
        schema = context_graph_client.get_schema()
        return schema
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return {"error": str(e)}

# List of tools to pass to Gemini
TOOLS = [
    search_customer,
    get_customer_decisions,
    find_similar_decisions,
    find_precedents,
    get_causal_chain,
    record_decision,
    detect_fraud_patterns,
    find_decision_community,
    get_policy,
    execute_cypher,
    get_schema,
]

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
# AGENT CLASS
# ============================================

class ContextGraphAgent:
    """Wrapper for managing Gemini Agent sessions."""

    def __init__(self):
        self.client = genai.Client(api_key=config.gemini.api_key)
        self.model_name = "gemini-2.5-flash-lite"
        self.system_instruction = CONTEXT_GRAPH_SYSTEM_PROMPT
        self.tools = TOOLS
        self.chat_session = None

    async def __aenter__(self):
        # The new SDK doesn't strictly need connect/disconnect like Claude Agent SDK
        # but we keep the interface for compatibility
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def _get_genai_history(self, conversation_history: List[Dict[str, str]]):
        history = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        return history

    async def query(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """Send a query to the agent and get the response."""
        history = self._get_genai_history(conversation_history or [])

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=history + [types.Content(role="user", parts=[types.Part(text=message)])],
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=self.tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        response_text = ""
        tool_calls = []

        # In non-streaming mode with automatic_function_calling,
        # Gemini might do multiple rounds. The final response is what we want.
        # However, to match the frontend expectation of tool_calls, we might need
        # to inspect the execution history if available, but for simplicity:

        if response.text:
            response_text = response.text

        # Extract tool calls from the candidate parts
        for part in response.candidates[0].content.parts:
            if part.function_call:
                tool_calls.append({
                    "name": part.function_call.name,
                    "input": part.function_call.args
                })

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "decisions_made": [], # Legacy, can be inferred from tool_calls
        }

    async def query_stream(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ):
        """Send a query to the agent and stream the response."""
        yield {"type": "agent_context", "context": {
            "system_prompt": self.system_instruction,
            "model": self.model_name,
            "available_tools": [tool.__name__ for tool in self.tools],
            "mcp_server": "gemini-native",
        }}

        history = self._get_genai_history(conversation_history or [])

        # For streaming with tool calls, we handle it manually to yield partial events
        # or use the internal chat session if it supports it.
        # Actually, google-genai supports automatic function calling in streams too.

        # We need to use a chat session to maintain state if we want multi-turn tool calling in one go
        chat = self.client.chats.create(
            model=self.model_name,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=self.tools,
            )
        )

        # We'll manually handle the loop to yield "tool_use" and "tool_result" events
        current_message = message
        all_tool_calls = []

        while True:
            # Send message and get stream
            stream = chat.send_message_stream(current_message)

            tool_calls_in_this_turn = []

            for chunk in stream:
                if chunk.text:
                    yield {"type": "text", "content": chunk.text}

                # Check for tool calls in this chunk
                for part in chunk.candidates[0].content.parts:
                    if part.function_call:
                        tc = {
                            "name": part.function_call.name,
                            "input": part.function_call.args
                        }
                        tool_calls_in_this_turn.append(tc)
                        all_tool_calls.append(tc)
                        yield {"type": "tool_use", **tc}

            if not tool_calls_in_this_turn:
                break

            # Execute tools and feed back to Gemini
            tool_responses = []
            for tc in tool_calls_in_this_turn:
                tool_func = next((t for t in self.tools if t.__name__ == tc["name"]), None)
                if tool_func:
                    try:
                        # Handle both sync and async tools if necessary,
                        # but our tools are defined as sync for Gemini compatibility in this context
                        # because google-genai expects sync functions for automatic calling usually,
                        # or we handle them here.
                        # All our defined tools above are now sync.
                        result = tool_func(**tc["input"])
                        yield {"type": "tool_result", "name": tc["name"], "output": result}
                        tool_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=tc["name"],
                                response=result
                            )
                        ))
                    except Exception as e:
                        error_msg = {"error": str(e)}
                        yield {"type": "tool_result", "name": tc["name"], "output": error_msg}
                        tool_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=tc["name"],
                                response=error_msg
                            )
                        ))
                else:
                    error_msg = {"error": f"Tool {tc['name']} not found"}
                    yield {"type": "tool_result", "name": tc["name"], "output": error_msg}
                    tool_responses.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=tc["name"],
                            response=error_msg
                        )
                    ))

            # Send tool responses back to Gemini
            current_message = types.Content(role="user", parts=tool_responses)

        yield {
            "type": "done",
            "tool_calls": all_tool_calls,
            "decisions_made": [],
        }
