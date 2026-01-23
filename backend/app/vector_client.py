"""
Neo4j vector search client using local Ollama.
Handles semantic similarity using nomic-embed-text via Ollama.
"""

from typing import Optional
import logging
from neo4j import GraphDatabase
import ollama

from .config import config
from .context_graph_client import convert_neo4j_value

logger = logging.getLogger(__name__)

class VectorClient:
    """Neo4j vector search client for semantic similarity using Ollama."""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.username, config.neo4j.password),
        )
        self.database = config.neo4j.database
        self.ollama_client = ollama.Client(host=config.ollama.base_url)
        self.model = config.ollama.model
        self.dimensions = config.ollama.dimensions

    def close(self):
        self.driver.close()

    # ============================================
    # EMBEDDING GENERATION
    # ============================================

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the given text using Ollama."""
        try:
            response = self.ollama_client.embed(
                model=self.model,
                input=text,
            )
            # The ollama-python library return format:
            # response.embeddings is a list of embeddings if input was a list or string?
            # Actually response['embeddings'][0] typically if it's the dict response
            # Let's check the library signature. Usually it's response.embeddings[0]
            if hasattr(response, 'embeddings') and response.embeddings:
                return response.embeddings[0]
            elif isinstance(response, dict) and 'embeddings' in response:
                return response['embeddings'][0]
            else:
                raise ValueError(f"Unexpected response format from Ollama: {response}")
        except Exception as e:
            logger.error(f"Error generating embedding with Ollama: {e}")
            raise

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.ollama_client.embed(
                model=self.model,
                input=texts,
            )
            if hasattr(response, 'embeddings'):
                return response.embeddings
            elif isinstance(response, dict) and 'embeddings' in response:
                return response['embeddings']
            else:
                raise ValueError(f"Unexpected response format from Ollama: {response}")
        except Exception as e:
            logger.error(f"Error generating batch embeddings with Ollama: {e}")
            raise

    # ============================================
    # SEMANTIC SEARCH
    # ============================================

    def search_decisions_semantic(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Search decisions by semantic similarity to query."""
        query_embedding = self.generate_embedding(query)

        category_filter = "WHERE d.category = $category" if category else ""

        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"""
                MATCH (d:Decision)
                {category_filter}
                CALL db.index.vector.queryNodes(
                    'decision_reasoning_idx',
                    $limit,
                    $query_embedding
                ) YIELD node, score
                WHERE node = d
                RETURN d.id AS id,
                       d.decision_type AS decision_type,
                       d.category AS category,
                       d.reasoning_summary AS reasoning_summary,
                       d.decision_timestamp AS decision_timestamp,
                       d.confidence_score AS confidence_score,
                       score AS semantic_similarity
                ORDER BY score DESC
                """,
                {
                    "query_embedding": query_embedding,
                    "limit": limit,
                    "category": category,
                },
            )
            return [convert_neo4j_value(dict(record)) for record in result]

    def search_policies_semantic(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """Search policies by semantic similarity."""
        query_embedding = self.generate_embedding(query)

        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                CALL db.index.vector.queryNodes(
                    'policy_description_idx',
                    $limit,
                    $query_embedding
                ) YIELD node, score
                RETURN node.id AS id,
                       node.name AS name,
                       node.description AS description,
                       node.category AS category,
                       score AS semantic_similarity
                ORDER BY score DESC
                """,
                {"query_embedding": query_embedding, "limit": limit},
            )
            return [convert_neo4j_value(dict(record)) for record in result]

    # ============================================
    # HYBRID SEARCH (Semantic + Structural)
    # ============================================

    def find_precedents_hybrid(
        self,
        scenario: str,
        category: Optional[str] = None,
        semantic_weight: float = 0.6,
        structural_weight: float = 0.4,
        limit: int = 5,
    ) -> list[dict]:
        """
        Find precedent decisions using semantic similarity.
        """
        query_embedding = self.generate_embedding(scenario)

        category_filter = "AND d.category = $category" if category else ""

        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"""
                CALL db.index.vector.queryNodes(
                    'decision_reasoning_idx',
                    $limit,
                    $query_embedding
                ) YIELD node AS d, score AS semantic_score
                WHERE d:Decision {category_filter}
                RETURN d.id AS id,
                       d.decision_type AS decision_type,
                       d.category AS category,
                       d.reasoning_summary AS reasoning_summary,
                       d.decision_timestamp AS decision_timestamp,
                       semantic_score AS combined_score,
                       semantic_score AS semantic_similarity,
                       null AS structural_similarity
                ORDER BY semantic_score DESC
                LIMIT $limit
                """,
                {
                    "query_embedding": query_embedding,
                    "category": category,
                    "limit": limit,
                },
            )
            return [convert_neo4j_value(dict(record)) for record in result]

    def find_similar_decisions_hybrid(
        self,
        decision_id: str,
        semantic_weight: float = 0.5,
        structural_weight: float = 0.5,
        limit: int = 5,
    ) -> list[dict]:
        """ Find decisions similar to a given decision using hybrid similarity. """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (source:Decision {id: $decision_id})
                WHERE source.reasoning_embedding IS NOT NULL
                  AND source.fastrp_embedding IS NOT NULL

                CALL db.index.vector.queryNodes(
                    'decision_reasoning_idx',
                    $limit * 2,
                    source.reasoning_embedding
                ) YIELD node AS semantic_match, score AS semantic_score
                WHERE semantic_match <> source

                CALL db.index.vector.queryNodes(
                    'decision_fastrp_idx',
                    $limit * 2,
                    source.fastrp_embedding
                ) YIELD node AS structural_match, score AS structural_score
                WHERE structural_match <> source

                WITH collect({
                    decision: semantic_match,
                    semantic: semantic_score,
                    structural: 0.0
                }) + collect({
                    decision: structural_match,
                    semantic: 0.0,
                    structural: structural_score
                }) AS all_matches

                UNWIND all_matches AS match
                WITH match.decision AS decision,
                     sum(match.semantic) AS total_semantic,
                     sum(match.structural) AS total_structural
                WHERE decision IS NOT NULL

                WITH decision,
                     total_semantic AS semantic_score,
                     total_structural AS structural_score,
                     (total_semantic * $semantic_weight + total_structural * $structural_weight) AS combined_score

                RETURN decision.id AS id,
                       decision.decision_type AS decision_type,
                       decision.category AS category,
                       decision.reasoning_summary AS reasoning_summary,
                       decision.decision_timestamp AS decision_timestamp,
                       combined_score,
                       semantic_score AS semantic_similarity,
                       structural_score AS structural_similarity
                ORDER BY combined_score DESC
                LIMIT $limit
                """,
                {
                    "decision_id": decision_id,
                    "semantic_weight": semantic_weight,
                    "structural_weight": structural_weight,
                    "limit": limit,
                },
            )
            return [convert_neo4j_value(dict(record)) for record in result]

    # ============================================
    # EMBEDDING STORAGE
    # ============================================

    def update_decision_reasoning_embedding(
        self,
        decision_id: str,
        reasoning: str,
    ) -> bool:
        """Generate and store reasoning embedding for a decision."""
        embedding = self.generate_embedding(reasoning)

        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (d:Decision {id: $decision_id})
                SET d.reasoning_embedding = $embedding
                RETURN d.id AS id
                """,
                {"decision_id": decision_id, "embedding": embedding},
            )
            return result.single() is not None

    def batch_update_decision_embeddings(
        self,
        limit: int = 100,
    ) -> int:
        """Generate embeddings for decisions that don't have them."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (d:Decision)
                WHERE d.reasoning_embedding IS NULL AND d.reasoning IS NOT NULL
                RETURN d.id AS id, d.reasoning AS reasoning
                LIMIT $limit
                """,
                {"limit": limit},
            )
            decisions = [dict(record) for record in result]

            if not decisions:
                return 0

            texts = [d["reasoning"] for d in decisions]
            embeddings = self.generate_embeddings_batch(texts)

            for decision, embedding in zip(decisions, embeddings):
                session.run(
                    """
                    MATCH (d:Decision {id: $decision_id})
                    SET d.reasoning_embedding = $embedding
                    """,
                    {"decision_id": decision["id"], "embedding": embedding},
                )

            return len(decisions)

# Singleton
vector_client = VectorClient()
