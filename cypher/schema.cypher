// ============================================
// CONTEXT GRAPH SCHEMA FOR FINANCIAL INSTITUTION
// ============================================
// This schema implements the "Event Clock" pattern from context graph theory
// Capturing decision traces alongside traditional entity data

// ============================================
// CONSTRAINTS - Unique IDs for all node types
// ============================================

CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT decision_context_id_unique IF NOT EXISTS FOR (dc:DecisionContext) REQUIRE dc.id IS UNIQUE;
CREATE CONSTRAINT precedent_id_unique IF NOT EXISTS FOR (p:Precedent) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT policy_id_unique IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT exception_id_unique IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT escalation_id_unique IF NOT EXISTS FOR (e:Escalation) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT support_ticket_id_unique IF NOT EXISTS FOR (s:SupportTicket) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT alert_id_unique IF NOT EXISTS FOR (a:Alert) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT agent_session_id_unique IF NOT EXISTS FOR (s:AgentSession) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT message_id_unique IF NOT EXISTS FOR (m:Message) REQUIRE m.id IS UNIQUE;

// ============================================
// TEXT INDEXES - For search queries
// ============================================

CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.normalized_name);
CREATE INDEX person_email_idx IF NOT EXISTS FOR (p:Person) ON (p.email);
CREATE INDEX organization_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.normalized_name);
CREATE INDEX account_number_idx IF NOT EXISTS FOR (a:Account) ON (a.account_number);
CREATE INDEX transaction_type_idx IF NOT EXISTS FOR (t:Transaction) ON (t.type);
CREATE INDEX decision_type_category_idx IF NOT EXISTS FOR (d:Decision) ON (d.decision_type, d.category);
CREATE INDEX decision_timestamp_idx IF NOT EXISTS FOR (d:Decision) ON (d.decision_timestamp);
CREATE INDEX transaction_timestamp_idx IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp);
CREATE INDEX policy_category_idx IF NOT EXISTS FOR (p:Policy) ON (p.category);

// ============================================
// VECTOR INDEXES - For semantic & structural similarity
// ============================================

// FastRP structural embeddings (128 dimensions)
CREATE VECTOR INDEX person_fastrp_idx IF NOT EXISTS
FOR (p:Person) ON (p.fastrp_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 128, `vector.similarity_function`: 'cosine'}};

CREATE VECTOR INDEX account_fastrp_idx IF NOT EXISTS
FOR (a:Account) ON (a.fastrp_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 128, `vector.similarity_function`: 'cosine'}};

CREATE VECTOR INDEX decision_fastrp_idx IF NOT EXISTS
FOR (d:Decision) ON (d.fastrp_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 128, `vector.similarity_function`: 'cosine'}};

CREATE VECTOR INDEX transaction_fastrp_idx IF NOT EXISTS
FOR (t:Transaction) ON (t.fastrp_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 128, `vector.similarity_function`: 'cosine'}};

// OpenAI text embeddings (1536 dimensions) for semantic search
CREATE VECTOR INDEX decision_reasoning_idx IF NOT EXISTS
FOR (d:Decision) ON (d.reasoning_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}};

CREATE VECTOR INDEX policy_description_idx IF NOT EXISTS
FOR (p:Policy) ON (p.description_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}};

// ============================================
// NODE TYPE DOCUMENTATION
// ============================================

// --- CORE ENTITIES (Identity-Resolved) ---

// Person - Unified customer/employee identity
// Properties:
//   id: string (UUID)
//   canonical_id: string (resolved identity ID for deduplication)
//   name: string
//   normalized_name: string (lowercase, for matching)
//   email: string
//   phone: string
//   date_of_birth: date
//   risk_score: float (0.0-1.0, computed)
//   source_systems: list<string> (e.g., ['CRM', 'Trading', 'Support'])
//   fastrp_embedding: list<float> (128 dims, structural)
//   created_at: datetime
//   updated_at: datetime

// Account - Bank accounts, trading accounts
// Properties:
//   id: string (UUID)
//   account_number: string
//   account_type: string ('checking', 'savings', 'trading', 'margin')
//   status: string ('active', 'frozen', 'closed')
//   balance: float
//   currency: string
//   risk_tier: string ('low', 'medium', 'high', 'critical')
//   opened_date: date
//   source_system: string
//   fastrp_embedding: list<float>
//   created_at: datetime
//   updated_at: datetime

// Transaction - Financial transactions
// Properties:
//   id: string (UUID)
//   transaction_id: string (external ID)
//   type: string ('deposit', 'withdrawal', 'transfer', 'trade')
//   amount: float
//   currency: string
//   timestamp: datetime
//   status: string ('pending', 'completed', 'flagged', 'reversed')
//   channel: string ('online', 'branch', 'atm', 'wire')
//   description: string
//   risk_score: float
//   source_system: string
//   fastrp_embedding: list<float>
//   created_at: datetime

// Organization - Companies, counterparties
// Properties:
//   id: string (UUID)
//   name: string
//   normalized_name: string
//   type: string ('corporation', 'bank', 'broker', 'vendor')
//   industry: string
//   country: string
//   risk_rating: string
//   sanctions_status: string ('clear', 'watchlist', 'blocked')
//   source_systems: list<string>
//   created_at: datetime
//   updated_at: datetime

// Employee - Staff members
// Properties:
//   id: string (UUID)
//   employee_id: string
//   name: string
//   department: string ('Trading', 'Compliance', 'Risk', 'Support')
//   role: string ('Analyst', 'Manager', 'Director', 'VP')
//   authorization_level: int (1-5)
//   created_at: datetime

// --- DECISION TRACE NODES (Event Clock) ---

// Decision - Core decision event with full context
// Properties:
//   id: string (UUID)
//   decision_type: string ('approval', 'rejection', 'escalation', 'exception', 'override', 'review')
//   category: string ('credit', 'fraud', 'compliance', 'trading', 'support', 'account_management')
//   status: string ('pending', 'approved', 'rejected', 'escalated')
//   decision_timestamp: datetime (THE EVENT CLOCK - when decision was made)
//   reasoning: string (full reasoning text - the decision trace)
//   reasoning_summary: string (brief summary)
//   confidence_score: float (0.0-1.0)
//   context_snapshot: string (JSON of relevant context at decision time)
//   risk_factors: list<string> (e.g., ['high_amount', 'new_account', 'unusual_pattern'])
//   source_system: string
//   session_id: string (agent session that made decision)
//   fastrp_embedding: list<float> (128 dims, structural similarity)
//   reasoning_embedding: list<float> (1536 dims, semantic similarity)
//   created_at: datetime

// DecisionContext - Snapshot of state at decision time
// Properties:
//   id: string (UUID)
//   decision_id: string
//   context_type: string ('customer_profile', 'account_state', 'market_conditions')
//   state_snapshot: string (JSON)
//   timestamp: datetime
//   created_at: datetime

// Precedent - Historical decisions used as reference
// Properties:
//   id: string (UUID)
//   description: string
//   outcome: string ('successful', 'failed', 'revised')
//   lessons_learned: string
//   created_at: datetime

// Policy - Rules and policies governing decisions
// Properties:
//   id: string (UUID)
//   name: string
//   description: string
//   category: string ('credit', 'fraud', 'compliance', 'trading')
//   version: string
//   effective_date: date
//   expiry_date: date
//   threshold_rules: string (JSON)
//   description_embedding: list<float>
//   created_at: datetime
//   updated_at: datetime

// Exception - Documented exceptions to normal process
// Properties:
//   id: string (UUID)
//   exception_type: string ('policy_override', 'limit_increase', 'manual_approval')
//   justification: string
//   risk_acceptance: string
//   expiry_date: datetime
//   created_at: datetime

// Escalation - Escalation events
// Properties:
//   id: string (UUID)
//   escalation_level: int (1, 2, 3)
//   reason: string
//   urgency: string ('low', 'medium', 'high', 'critical')
//   resolution: string
//   resolution_time_hours: float
//   created_at: datetime
//   resolved_at: datetime

// --- SUPPORT/OPERATIONAL NODES ---

// SupportTicket - Customer support cases
// Properties:
//   id: string (UUID)
//   ticket_id: string
//   category: string ('dispute', 'inquiry', 'complaint', 'fraud_report')
//   priority: string
//   status: string
//   description: string
//   resolution: string
//   sentiment_score: float
//   created_at: datetime
//   resolved_at: datetime

// Alert - System-generated alerts
// Properties:
//   id: string (UUID)
//   alert_type: string ('fraud', 'aml', 'credit', 'market')
//   severity: string ('low', 'medium', 'high', 'critical')
//   description: string
//   status: string ('open', 'investigating', 'closed', 'false_positive')
//   source_system: string
//   created_at: datetime
//   resolved_at: datetime

// AgentSession - AI agent conversation sessions
// Properties:
//   id: string (UUID)
//   session_type: string ('customer_service', 'fraud_review', 'credit_decision')
//   started_at: datetime
//   ended_at: datetime
//   message_count: int
//   decisions_made: int
//   outcome: string

// Message - Individual messages in session
// Properties:
//   id: string (UUID)
//   session_id: string
//   role: string ('user', 'agent', 'system')
//   content: string
//   timestamp: datetime
//   tool_calls: string (JSON of tool calls made)

// ============================================
// RELATIONSHIP TYPE DOCUMENTATION
// ============================================

// --- Entity Relationships ---
// (:Person)-[:OWNS]->(:Account)
// (:Person)-[:WORKS_FOR]->(:Organization)
// (:Person)-[:RELATED_TO {relationship_type: 'spouse'|'beneficiary'|'authorized_signer'}]->(:Person)
// (:Account)-[:HELD_AT]->(:Organization)
// (:Transaction)-[:FROM_ACCOUNT]->(:Account)
// (:Transaction)-[:TO_ACCOUNT]->(:Account)
// (:Transaction)-[:INVOLVING]->(:Organization)
// (:Employee)-[:WORKS_IN]->(:Organization)

// --- Decision Trace Relationships (CAUSAL DAG) ---
// (:Decision)-[:ABOUT]->(:Person|:Account|:Transaction|:Organization)
// (:Decision)-[:MADE_BY]->(:Employee|:AgentSession)
// (:Decision)-[:CAUSED {causation_type, confidence, lag_time_hours}]->(:Decision)
// (:Decision)-[:INFLUENCED {influence_type, weight}]->(:Decision)
// (:Decision)-[:PRECEDENT_FOR {similarity_score, outcome_relevance}]->(:Decision)
// (:Decision)-[:APPLIED_POLICY]->(:Policy)
// (:Decision)-[:GRANTED_EXCEPTION]->(:Exception)
// (:Decision)-[:TRIGGERED]->(:Escalation)
// (:Decision)-[:HAD_CONTEXT]->(:DecisionContext)
// (:Decision)-[:FOLLOWED_PRECEDENT]->(:Precedent)

// --- Support Relationships ---
// (:SupportTicket)-[:RAISED_BY]->(:Person)
// (:SupportTicket)-[:REGARDING]->(:Account|:Transaction)
// (:SupportTicket)-[:HANDLED_BY]->(:Employee)
// (:SupportTicket)-[:RESULTED_IN]->(:Decision)
// (:Alert)-[:REGARDING]->(:Person|:Account|:Transaction)
// (:Alert)-[:TRIGGERED]->(:Decision)

// --- Agent/Session Relationships ---
// (:AgentSession)-[:HAS_MESSAGE]->(:Message)
// (:Message)-[:NEXT_MESSAGE]->(:Message)
// (:Message)-[:MADE_DECISION]->(:Decision)

// --- Entity Resolution Relationships ---
// (:Person)-[:SAME_AS {confidence, resolution_method, resolved_at}]->(:Person)
// (:Organization)-[:SAME_AS]->(:Organization)
