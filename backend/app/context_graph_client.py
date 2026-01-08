"""
Neo4j client for context graph operations.
Handles entities, decisions, and causal relationships.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .config import config
from .models import (
    Account,
    CausalChain,
    Decision,
    GraphData,
    GraphNode,
    GraphRelationship,
    Person,
    Transaction,
)


class ContextGraphClient:
    """Neo4j client for context graph operations."""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.username, config.neo4j.password),
        )
        self.database = config.neo4j.database

    def close(self):
        self.driver.close()

    def verify_connectivity(self) -> bool:
        """Verify connection to Neo4j."""
        try:
            self.driver.verify_connectivity()
            return True
        except ServiceUnavailable:
            return False

    # ============================================
    # CUSTOMER/PERSON OPERATIONS
    # ============================================

    def search_customers(self, query: str, limit: int = 10) -> list[dict]:
        """Search for customers by name, email, or account number."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (p:Person)
                WHERE toLower(p.name) CONTAINS toLower($query)
                   OR toLower(p.email) CONTAINS toLower($query)
                   OR EXISTS {
                       MATCH (p)-[:OWNS]->(a:Account)
                       WHERE a.account_number CONTAINS $query
                   }
                OPTIONAL MATCH (p)-[:OWNS]->(a:Account)
                OPTIONAL MATCH (d:Decision)-[:ABOUT]->(p)
                RETURN p.id AS id,
                       p.name AS name,
                       p.email AS email,
                       p.risk_score AS risk_score,
                       count(DISTINCT a) AS account_count,
                       count(DISTINCT d) AS decision_count
                ORDER BY p.risk_score DESC
                LIMIT $limit
                """,
                {"query": query, "limit": limit},
            )
            return [dict(record) for record in result]

    def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get a customer by ID with related entities."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (p:Person {id: $customer_id})
                OPTIONAL MATCH (p)-[:OWNS]->(a:Account)
                OPTIONAL MATCH (p)-[:WORKS_FOR]->(o:Organization)
                RETURN p {
                    .*,
                    accounts: collect(DISTINCT a {.*}),
                    organizations: collect(DISTINCT o {.*})
                } AS customer
                """,
                {"customer_id": customer_id},
            )
            record = result.single()
            return record["customer"] if record else None

    def get_customer_decisions(
        self,
        customer_id: str,
        decision_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get all decisions made about a customer."""
        type_filter = "AND d.decision_type = $decision_type" if decision_type else ""

        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"""
                MATCH (d:Decision)-[:ABOUT]->(p:Person {{id: $customer_id}})
                WHERE true {type_filter}
                OPTIONAL MATCH (d)-[:MADE_BY]->(maker)
                OPTIONAL MATCH (d)-[:APPLIED_POLICY]->(policy:Policy)
                RETURN d {{
                    .*,
                    made_by: maker.name,
                    policies_applied: collect(DISTINCT policy.name)
                }} AS decision
                ORDER BY d.decision_timestamp DESC
                LIMIT $limit
                """,
                {
                    "customer_id": customer_id,
                    "decision_type": decision_type,
                    "limit": limit,
                },
            )
            return [record["decision"] for record in result]

    # ============================================
    # DECISION OPERATIONS
    # ============================================

    def get_decision(self, decision_id: str) -> Optional[dict]:
        """Get a decision by ID with full context."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (d:Decision {id: $decision_id})
                OPTIONAL MATCH (d)-[:ABOUT]->(entity)
                OPTIONAL MATCH (d)-[:MADE_BY]->(maker)
                OPTIONAL MATCH (d)-[:APPLIED_POLICY]->(policy:Policy)
                OPTIONAL MATCH (d)-[:GRANTED_EXCEPTION]->(exception:Exception)
                OPTIONAL MATCH (d)-[:TRIGGERED]->(escalation:Escalation)
                OPTIONAL MATCH (d)-[:HAD_CONTEXT]->(context:DecisionContext)
                RETURN d {
                    .*,
                    about_entities: collect(DISTINCT {id: entity.id, labels: labels(entity), name: entity.name}),
                    made_by: maker {.*},
                    policies: collect(DISTINCT policy {.*}),
                    exceptions: collect(DISTINCT exception {.*}),
                    escalations: collect(DISTINCT escalation {.*}),
                    contexts: collect(DISTINCT context {.*})
                } AS decision
                """,
                {"decision_id": decision_id},
            )
            record = result.single()
            return record["decision"] if record else None

    def record_decision(
        self,
        decision_type: str,
        category: str,
        reasoning: str,
        customer_id: Optional[str] = None,
        account_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        risk_factors: list[str] = None,
        precedent_ids: list[str] = None,
        confidence_score: float = 0.8,
        session_id: Optional[str] = None,
        reasoning_embedding: Optional[list[float]] = None,
    ) -> str:
        """Record a new decision with full context."""
        decision_id = str(uuid.uuid4())
        risk_factors = risk_factors or []
        precedent_ids = precedent_ids or []

        with self.driver.session(database=self.database) as session:
            # Create the decision
            session.run(
                """
                CREATE (d:Decision {
                    id: $decision_id,
                    decision_type: $decision_type,
                    category: $category,
                    status: 'completed',
                    decision_timestamp: datetime(),
                    reasoning: $reasoning,
                    reasoning_summary: $reasoning_summary,
                    confidence_score: $confidence_score,
                    risk_factors: $risk_factors,
                    session_id: $session_id,
                    reasoning_embedding: $reasoning_embedding,
                    created_at: datetime()
                })
                """,
                {
                    "decision_id": decision_id,
                    "decision_type": decision_type,
                    "category": category,
                    "reasoning": reasoning,
                    "reasoning_summary": reasoning[:100] + "..."
                    if len(reasoning) > 100
                    else reasoning,
                    "confidence_score": confidence_score,
                    "risk_factors": risk_factors,
                    "session_id": session_id,
                    "reasoning_embedding": reasoning_embedding,
                },
            )

            # Link to customer
            if customer_id:
                session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH (p:Person {id: $customer_id})
                    MERGE (d)-[:ABOUT]->(p)
                    """,
                    {"decision_id": decision_id, "customer_id": customer_id},
                )

            # Link to account
            if account_id:
                session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH (a:Account {id: $account_id})
                    MERGE (d)-[:ABOUT]->(a)
                    """,
                    {"decision_id": decision_id, "account_id": account_id},
                )

            # Link to transaction
            if transaction_id:
                session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH (t:Transaction {id: $transaction_id})
                    MERGE (d)-[:ABOUT]->(t)
                    """,
                    {"decision_id": decision_id, "transaction_id": transaction_id},
                )

            # Link to precedents
            for precedent_id in precedent_ids:
                session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH (p:Decision {id: $precedent_id})
                    MERGE (d)-[:FOLLOWED_PRECEDENT]->(p)
                    """,
                    {"decision_id": decision_id, "precedent_id": precedent_id},
                )

        return decision_id

    def get_causal_chain(
        self,
        decision_id: str,
        direction: str = "both",
        depth: int = 3,
    ) -> dict:
        """Trace the causal chain of a decision."""
        with self.driver.session(database=self.database) as session:
            causes = []
            effects = []

            if direction in ("both", "causes"):
                result = session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH path = (cause:Decision)-[:CAUSED|INFLUENCED*1..$depth]->(d)
                    WITH cause, length(path) AS distance
                    RETURN cause {.*, distance: distance} AS decision
                    ORDER BY distance
                    """,
                    {"decision_id": decision_id, "depth": depth},
                )
                causes = [record["decision"] for record in result]

            if direction in ("both", "effects"):
                result = session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    MATCH path = (d)-[:CAUSED|INFLUENCED*1..$depth]->(effect:Decision)
                    WITH effect, length(path) AS distance
                    RETURN effect {.*, distance: distance} AS decision
                    ORDER BY distance
                    """,
                    {"decision_id": decision_id, "depth": depth},
                )
                effects = [record["decision"] for record in result]

            return {
                "decision_id": decision_id,
                "causes": causes,
                "effects": effects,
                "depth": depth,
            }

    # ============================================
    # POLICY OPERATIONS
    # ============================================

    def get_policies(self, category: Optional[str] = None) -> list[dict]:
        """Get policies, optionally filtered by category."""
        category_filter = "WHERE p.category = $category" if category else ""

        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"""
                MATCH (p:Policy)
                {category_filter}
                RETURN p {{.*}} AS policy
                ORDER BY p.name
                """,
                {"category": category},
            )
            return [record["policy"] for record in result]

    def get_policy(self, policy_id: str) -> Optional[dict]:
        """Get a policy by ID."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (p:Policy {id: $policy_id})
                OPTIONAL MATCH (d:Decision)-[:APPLIED_POLICY]->(p)
                RETURN p {
                    .*,
                    usage_count: count(d)
                } AS policy
                """,
                {"policy_id": policy_id},
            )
            record = result.single()
            return record["policy"] if record else None

    # ============================================
    # GRAPH VISUALIZATION
    # ============================================

    def get_graph_data(
        self,
        center_node_id: Optional[str] = None,
        center_node_type: Optional[str] = None,
        depth: int = 2,
        include_decisions: bool = True,
        limit: int = 100,
    ) -> GraphData:
        """Get graph data for NVL visualization."""
        with self.driver.session(database=self.database) as session:
            if center_node_id and center_node_type:
                # Get subgraph centered on a specific node
                result = session.run(
                    f"""
                    MATCH (center:{center_node_type} {{id: $center_id}})
                    CALL apoc.path.subgraphAll(center, {{
                        maxLevel: $depth,
                        relationshipFilter: null,
                        labelFilter: null
                    }})
                    YIELD nodes, relationships
                    UNWIND nodes AS node
                    WITH collect(DISTINCT node) AS allNodes, relationships
                    UNWIND relationships AS rel
                    WITH allNodes, collect(DISTINCT rel) AS allRels
                    RETURN allNodes[0..$limit] AS nodes, allRels AS relationships
                    """,
                    {"center_id": center_node_id, "depth": depth, "limit": limit},
                )
            else:
                # Get a sample of the graph
                decision_filter = "" if include_decisions else "WHERE NOT 'Decision' IN labels(n)"
                result = session.run(
                    f"""
                    MATCH (n)
                    {decision_filter}
                    WITH n LIMIT $limit
                    OPTIONAL MATCH (n)-[r]-(m)
                    WITH collect(DISTINCT n) + collect(DISTINCT m) AS nodes,
                         collect(DISTINCT r) AS relationships
                    RETURN nodes, relationships
                    """,
                    {"limit": limit},
                )

            record = result.single()
            if not record:
                return GraphData(nodes=[], relationships=[])

            nodes = []
            for node in record["nodes"] or []:
                if node:
                    nodes.append(
                        GraphNode(
                            id=str(node.element_id),
                            labels=list(node.labels),
                            properties=dict(node),
                        )
                    )

            relationships = []
            for rel in record["relationships"] or []:
                if rel:
                    relationships.append(
                        GraphRelationship(
                            id=str(rel.element_id),
                            type=rel.type,
                            start_node_id=str(rel.start_node.element_id),
                            end_node_id=str(rel.end_node.element_id),
                            properties=dict(rel),
                        )
                    )

            return GraphData(nodes=nodes, relationships=relationships)

    # ============================================
    # STATISTICS
    # ============================================

    def get_statistics(self) -> dict:
        """Get graph statistics."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (n)
                WITH labels(n) AS nodeLabels
                UNWIND nodeLabels AS label
                WITH label, count(*) AS count
                RETURN collect({label: label, count: count}) AS node_counts
                """
            )
            record = result.single()
            node_counts = {item["label"]: item["count"] for item in record["node_counts"]}

            result = session.run(
                """
                MATCH ()-[r]->()
                WITH type(r) AS relType
                WITH relType, count(*) AS count
                RETURN collect({type: relType, count: count}) AS rel_counts
                """
            )
            record = result.single()
            rel_counts = {item["type"]: item["count"] for item in record["rel_counts"]}

            return {
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "total_nodes": sum(node_counts.values()),
                "total_relationships": sum(rel_counts.values()),
            }

    # ============================================
    # CYPHER EXECUTION (Read-only)
    # ============================================

    def execute_cypher(self, cypher: str, parameters: dict = None) -> list[dict]:
        """Execute a read-only Cypher query."""
        # Basic safety check - only allow read operations
        cypher_upper = cypher.upper().strip()
        if any(
            keyword in cypher_upper
            for keyword in ["CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP"]
        ):
            raise ValueError("Only read operations are allowed")

        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, parameters or {})
            return [dict(record) for record in result]


# Singleton instance
context_graph_client = ContextGraphClient()
