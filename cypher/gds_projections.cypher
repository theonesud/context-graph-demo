// ============================================
// GDS GRAPH PROJECTIONS AND ALGORITHMS
// ============================================
// Neo4j Graph Data Science algorithms for context graph analysis
// Key differentiator: FastRP for structural similarity (not possible on Postgres)

// ============================================
// GRAPH PROJECTIONS
// ============================================

// Project the full decision graph for analysis
CALL gds.graph.project(
  'decision-graph',
  ['Decision', 'Person', 'Account', 'Transaction', 'Organization', 'Policy', 'Employee'],
  {
    ABOUT: {orientation: 'UNDIRECTED'},
    CAUSED: {orientation: 'NATURAL', properties: ['confidence']},
    INFLUENCED: {orientation: 'NATURAL', properties: ['weight']},
    PRECEDENT_FOR: {orientation: 'NATURAL', properties: ['similarity_score']},
    OWNS: {orientation: 'UNDIRECTED'},
    MADE_BY: {orientation: 'NATURAL'},
    APPLIED_POLICY: {orientation: 'NATURAL'},
    FROM_ACCOUNT: {orientation: 'NATURAL'},
    TO_ACCOUNT: {orientation: 'NATURAL'}
  }
) YIELD graphName, nodeCount, relationshipCount;

// Project entity graph for fraud detection
CALL gds.graph.project(
  'entity-graph',
  ['Person', 'Account', 'Transaction', 'Organization'],
  {
    OWNS: {orientation: 'UNDIRECTED'},
    FROM_ACCOUNT: {orientation: 'NATURAL'},
    TO_ACCOUNT: {orientation: 'NATURAL'},
    INVOLVING: {orientation: 'UNDIRECTED'},
    RELATED_TO: {orientation: 'UNDIRECTED'}
  }
) YIELD graphName, nodeCount, relationshipCount;

// ============================================
// FASTRP EMBEDDINGS
// ============================================
// FastRP is 75,000x faster than node2vec with equivalent accuracy
// Captures structural/topological similarity

// Generate FastRP embeddings for decision graph
CALL gds.fastRP.mutate('decision-graph', {
  embeddingDimension: 128,
  iterationWeights: [0.0, 1.0, 1.0, 0.8, 0.6],
  normalizationStrength: 0.5,
  randomSeed: 42,
  mutateProperty: 'fastrp_embedding'
}) YIELD nodePropertiesWritten, computeMillis;

// Write FastRP embeddings back to database
CALL gds.graph.nodeProperties.write(
  'decision-graph',
  ['fastrp_embedding'],
  ['Decision', 'Person', 'Account', 'Transaction']
) YIELD propertiesWritten;

// Generate FastRP for entity graph (fraud detection)
CALL gds.fastRP.mutate('entity-graph', {
  embeddingDimension: 128,
  iterationWeights: [0.0, 1.0, 1.0, 0.8, 0.6],
  normalizationStrength: 0.5,
  randomSeed: 42,
  mutateProperty: 'fastrp_embedding'
}) YIELD nodePropertiesWritten, computeMillis;

// ============================================
// K-NEAREST NEIGHBORS (KNN)
// ============================================
// Find similar nodes based on FastRP embeddings

// Run KNN on decisions using FastRP embeddings
CALL gds.knn.stream('decision-graph', {
  nodeLabels: ['Decision'],
  nodeProperties: ['fastrp_embedding'],
  topK: 10,
  sampleRate: 1.0,
  deltaThreshold: 0.001,
  randomSeed: 42
}) YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS decision1, gds.util.asNode(node2) AS decision2, similarity
RETURN decision1.id AS source_id, decision2.id AS target_id, similarity
ORDER BY similarity DESC;

// Create KNN similarity relationships (optional - for caching)
CALL gds.knn.mutate('decision-graph', {
  nodeLabels: ['Decision'],
  nodeProperties: ['fastrp_embedding'],
  topK: 5,
  mutateRelationshipType: 'SIMILAR_TO',
  mutateProperty: 'score'
}) YIELD relationshipsWritten;

// ============================================
// NODE SIMILARITY
// ============================================
// Find nodes with similar neighborhood structures
// Great for fraud pattern detection

// Run Node Similarity on accounts
CALL gds.nodeSimilarity.stream('entity-graph', {
  nodeLabels: ['Account'],
  topK: 10,
  similarityCutoff: 0.5
}) YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS account1, gds.util.asNode(node2) AS account2, similarity
RETURN account1.account_number AS account1, account2.account_number AS account2, similarity
ORDER BY similarity DESC;

// Node Similarity for persons (entity resolution)
CALL gds.nodeSimilarity.stream('entity-graph', {
  nodeLabels: ['Person'],
  topK: 10,
  similarityCutoff: 0.7
}) YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS person1, gds.util.asNode(node2) AS person2, similarity
WHERE person1.id < person2.id  // Avoid duplicates
RETURN person1.name AS person1, person2.name AS person2, similarity
ORDER BY similarity DESC;

// ============================================
// LOUVAIN COMMUNITY DETECTION
// ============================================
// Cluster related decisions into communities

CALL gds.louvain.stream('decision-graph', {
  nodeLabels: ['Decision'],
  relationshipTypes: ['CAUSED', 'INFLUENCED', 'PRECEDENT_FOR']
}) YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS decision, communityId
RETURN communityId,
       count(decision) AS decision_count,
       collect(DISTINCT decision.decision_type) AS decision_types,
       collect(DISTINCT decision.category) AS categories
ORDER BY decision_count DESC
LIMIT 10;

// Write community IDs back to nodes
CALL gds.louvain.mutate('decision-graph', {
  nodeLabels: ['Decision'],
  relationshipTypes: ['CAUSED', 'INFLUENCED', 'PRECEDENT_FOR'],
  mutateProperty: 'community_id'
}) YIELD communityCount, modularity;

// ============================================
// PAGERANK - INFLUENCE SCORING
// ============================================
// Rank decisions by influence (how many other decisions they affected)

CALL gds.pageRank.stream('decision-graph', {
  nodeLabels: ['Decision'],
  relationshipTypes: ['CAUSED', 'INFLUENCED'],
  maxIterations: 20,
  dampingFactor: 0.85
}) YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS decision, score
WHERE decision.decision_type IN ['exception', 'override', 'escalation']
RETURN decision.id, decision.decision_type, decision.reasoning_summary, score AS influence_score
ORDER BY score DESC
LIMIT 20;

// Write PageRank scores to nodes
CALL gds.pageRank.mutate('decision-graph', {
  nodeLabels: ['Decision'],
  relationshipTypes: ['CAUSED', 'INFLUENCED'],
  mutateProperty: 'influence_score'
}) YIELD nodePropertiesWritten;

// ============================================
// UTILITY QUERIES
// ============================================

// Drop graph projections (cleanup)
CALL gds.graph.drop('decision-graph', false) YIELD graphName;
CALL gds.graph.drop('entity-graph', false) YIELD graphName;

// List all graph projections
CALL gds.graph.list() YIELD graphName, nodeCount, relationshipCount;

// ============================================
// USE CASE: FIND SIMILAR DECISIONS
// ============================================
// Given a decision, find structurally similar past decisions

// Example: Find decisions similar to a specific one
MATCH (current:Decision {id: $decision_id})
CALL db.index.vector.queryNodes('decision_fastrp_idx', 10, current.fastrp_embedding)
YIELD node AS similar, score
WHERE similar.id <> current.id
MATCH (similar)-[:ABOUT]->(entity)
OPTIONAL MATCH (similar)<-[:CAUSED]-(cause:Decision)
OPTIONAL MATCH (similar)-[:CAUSED]->(effect:Decision)
RETURN similar.id,
       similar.decision_type,
       similar.reasoning_summary,
       collect(DISTINCT labels(entity)) AS affected_entities,
       collect(DISTINCT cause.decision_type) AS caused_by,
       collect(DISTINCT effect.decision_type) AS led_to,
       score AS similarity
ORDER BY score DESC
LIMIT 5;

// ============================================
// USE CASE: FRAUD PATTERN DETECTION
// ============================================
// Compare account structures to known fraud patterns

// Find accounts with similar transaction patterns to flagged accounts
MATCH (fraud:Account)-[:FROM_ACCOUNT|TO_ACCOUNT]-(t:Transaction)
WHERE t.status = 'flagged'
WITH fraud, count(t) AS flagged_count
WHERE flagged_count >= 3
CALL db.index.vector.queryNodes('account_fastrp_idx', 20, fraud.fastrp_embedding)
YIELD node AS suspect, score
WHERE suspect.id <> fraud.id AND suspect.risk_tier <> 'critical'
RETURN suspect.account_number, suspect.risk_tier, score AS structural_similarity
ORDER BY score DESC
LIMIT 10;

// ============================================
// USE CASE: ENTITY RESOLUTION
// ============================================
// Find potential duplicate persons using structural similarity

MATCH (p1:Person), (p2:Person)
WHERE p1.id < p2.id
  AND p1.normalized_name = p2.normalized_name
WITH p1, p2
CALL db.index.vector.queryNodes('person_fastrp_idx', 1, p1.fastrp_embedding)
YIELD node, score
WHERE node.id = p2.id
RETURN p1.name AS person1,
       p2.name AS person2,
       p1.source_systems AS sources1,
       p2.source_systems AS sources2,
       score AS structural_similarity
ORDER BY score DESC;

// ============================================
// USE CASE: HYBRID SEARCH (Semantic + Structural)
// ============================================
// Combine text embeddings with graph structure for best results

// Find precedents using both semantic and structural similarity
MATCH (d:Decision)
WHERE d.category = $category
// Semantic similarity on reasoning text
CALL db.index.vector.queryNodes('decision_reasoning_idx', 20, $query_embedding)
YIELD node AS semantic_match, score AS semantic_score
WHERE semantic_match.id = d.id
// Structural similarity on graph position
WITH d, semantic_score
CALL db.index.vector.queryNodes('decision_fastrp_idx', 20, d.fastrp_embedding)
YIELD node AS structural_match, score AS structural_score
// Combine scores
RETURN structural_match.id,
       structural_match.decision_type,
       structural_match.reasoning_summary,
       semantic_score,
       structural_score,
       (semantic_score * 0.6 + structural_score * 0.4) AS combined_score
ORDER BY combined_score DESC
LIMIT 5;
