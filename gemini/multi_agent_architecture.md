# Multi-Agent Auditor System - Implementation Plan
## **I. High-Level Architecture**

### **Agent Hierarchy**
```
Input (Product Data + Context)
    ↓
┌─────────────────────────────────────┐
│   Specialized Agents (Parallel)    │
├─────────────────────────────────────┤
│  1. Photo Agent                     │
│  2. Title Validation Agent          │
│  3. Specs Validation Agent          │
└─────────────────────────────────────┘
    ↓ (Structured Outputs)
┌─────────────────────────────────────┐
│   Master Decision Agent (Light)     │
│   - Decision Grid Logic             │
│   - Rule-based Aggregation          │
└─────────────────────────────────────┘
    ↓
Final Audit Result
```

---

## **II. Agent Responsibilities Breakdown**

### **1. Photo Agent**
**Handles:** Tasks 1, 2, 3, and portions of Task 6, 8, 9, 10 related to images

**Input:**
- Product Photo (image)
- Relevant Photos (category examples)
- Irrelevant Photos (anti-examples)

**Processing:**
- Primary object detection
- OCR extraction
- Visibility assessment (all 3a-3e criteria)
- Brand/model recognition from image
- Category alignment checks (9a, 9b, 10c)

**Output (Structured JSON):**
```json
{
  "primary_object": "string",
  "ocr_text": "string",
  "visibility_flags": {
    "severely_cut_off": "outlier/not_outlier/can't_say",
    "unidentifiable_blur": "...",
    "severely_obscured": "...",
    "generally_unclear": "...",
    "human_blocking": "..."
  },
  "photo_quality_error": "boolean",
  "category_alignment": {
    "matches_relevant_photos": "yes/no/can't_say",
    "matches_irrelevant_photos": "yes/no/can't_say"
  },
  "brands_detected": ["brand1", "brand2"],
  "reasons": {...}
}
```

---

### **2. Title Validation Agent**
**Handles:** Task 4, portions of Task 6, 8, 9, 10 related to titles

**Input:**
- Product Title (text)
- Relevant Titles (category examples)
- Irrelevant Titles (anti-examples)

**Processing:**
- Spell checking
- Duplicate word detection
- Internal contradiction analysis
- Brand/model extraction from title
- Category keyword matching (9e, 9f, 10a)

**Output (Structured JSON):**
```json
{
  "quality_checks": {
    "spell_error": "outlier/not_outlier/can't_say",
    "duplicate_words": "outlier/not_outlier/can't_say"
  },
  "title_quality_error": "boolean",
  "contradiction_checks": {
    "internal_contradiction": "outlier/not_outlier/can't_say"
  },
  "title_contradiction_error": "boolean",
  "category_alignment": {
    "matches_relevant_titles": "yes/no/can't_say",
    "better_categorized_as": ["category1", "category2"] or null
  },
  "entities_extracted": ["entity1", "entity2"],
  "reasons": {...}
}
```

---

### **3. Specs Validation Agent**
**Handles:** Task 5, portions of Task 6, 8

**Input:**
- Product Specifications (text)
- Product Title (for cross-validation)

**Processing:**
- Spell checking
- Duplicate specification detection
- Internal contradiction analysis
- Entity/brand extraction from specs

**Output (Structured JSON):**
```json
{
  "quality_checks": {
    "spell_error": "outlier/not_outlier/can't_say",
    "duplicate_specs": "outlier/not_outlier/can't_say"
  },
  "specs_quality_error": "boolean",
  "contradiction_checks": {
    "internal_contradiction": "outlier/not_outlier/can't_say"
  },
  "specs_contradiction_error": "boolean",
  "entities_extracted": ["entity1", "entity2"],
  "reasons": {...}
}
```

---

### **4. Master Decision Agent (Lightweight)**
**Handles:** Task 7, 8 (cross-agent contradictions), final aggregation

**Input:**
- Outputs from all 3 specialized agents
- Decision grid configuration (from backend config)

**Processing:**
- Construct Product Search Query (Task 7) from combined entities
- Detect cross-domain contradictions:
  - Photo-Title (8a, 8e)
  - Photo-Specs (8b)
  - Title-Specs (8c)
  - Within search query (8d)
  - Category contradictions (9c, 9d, 10b, 10d)
- Apply decision grid rules (rule-based, not LLM-heavy)

**Output (Final Decision):**
```json
{
  "product_search_query": "string",
  "cross_validation": {
    "photo_title_contradiction": "yes/no/can't_say",
    "photo_specs_contradiction": "yes/no/can't_say",
    "title_specs_contradiction": "yes/no/can't_say",
    "search_query_contradiction": "yes/no/can't_say"
  },
  "final_errors": {
    "photo_quality_error": "boolean",
    "title_quality_error": "boolean",
    "title_contradiction_error": "boolean",
    "specs_quality_error": "boolean",
    "specs_contradiction_error": "boolean",
    "photo_category_error": "boolean",
    "title_category_error": "boolean",
    "category_contradiction_error": "boolean"
  },
  "audit_decision": "PASS/FAIL/REVIEW",
  "confidence_score": 0.85,
  "reasons": {...}
}
```

---

## **III. Backend Implementation Strategy**

### **A. Service Layer Architecture** (`app/services/`)

Create these new services:

1. **`multi_agent_orchestrator.py`**
   - Main entry point for the multi-agent system
   - Orchestrates parallel execution of specialized agents
   - Aggregates results and invokes master agent
   - Handles error recovery and fallback logic

2. **`agents/photo_agent.py`**
   - Vision model integration (Gemini Vision or similar)
   - OCR processing
   - Image analysis logic

3. **`agents/title_agent.py`**
   - Text analysis using lightweight LLM
   - Keyword extraction
   - Spell checking utilities

4. **`agents/specs_agent.py`**
   - Similar to title agent but specs-focused
   - May share some utilities with title agent

5. **`agents/master_agent.py`**
   - **Lightweight LLM or rule engine**
   - Decision grid implementation
   - Cross-validation logic

6. **`decision_grid.py`**
   - Configuration-driven decision matrix
   - Maps error combinations to outcomes
   - Allows easy rule updates without code changes

### **B. Decision Grid Design**

Store decision rules in configuration (JSON/YAML in `app/core/config.py` or separate file):

```python
decision_grid = {
    "rules": [
        {
            "condition": {
                "photo_quality_error": True,
                "title_quality_error": False,
                "category_error": False
            },
            "action": "FAIL",
            "reason": "Photo quality standards not met",
            "confidence": 0.95
        },
        {
            "condition": {
                "photo_category_error": True,
                "title_category_error": True
            },
            "action": "FAIL",
            "reason": "Product miscategorized across multiple signals",
            "confidence": 0.98
        },
        {
            "condition": {
                "title_quality_error": True,
                "specs_quality_error": False,
                "ALL_other_errors": False
            },
            "action": "REVIEW",
            "reason": "Minor title issues require human verification",
            "confidence": 0.70
        }
        // ... more rules
    ],
    "default_action": "REVIEW"
}
```

### **C. API Layer Updates** (`app/api/v1/`)

Create new endpoints:

1. **`/audit/multi-agent`** (POST)
   - Accepts same input as current auditor
   - Routes to multi-agent orchestrator
   - Returns structured audit result

2. **`/audit/agent-details/{audit_id}`** (GET)
   - Returns individual agent outputs for transparency
   - Useful for debugging and UI display

3. **`/admin/decision-grid`** (GET/PUT)
   - View and update decision grid rules
   - Admin-only endpoint

### **D. Data Models** (`app/schemas/`)

Create Pydantic models for:

1. **`AgentRequest`** - Input to each specialized agent
2. **`PhotoAgentResponse`** - Photo agent output
3. **`TitleAgentResponse`** - Title agent output
4. **`SpecsAgentResponse`** - Specs agent output
5. **`MasterAgentResponse`** - Final decision
6. **`MultiAgentAuditResult`** - Complete audit with all agent outputs

---

## **IV. Frontend Integration** (`streamlit_app/`)

### **A. UI Enhancements**

1. **Main Audit Page**
   - Update to call `/audit/multi-agent` endpoint
   - Display agent-level results in expandable sections
   - Show decision grid reasoning

2. **Agent Details View** (new page: `pages/agent_analysis.py`)
   - Tabs for each agent's analysis
   - Visual indicators for errors/passes
   - Trace decision path through the grid

3. **Admin Panel** (new page: `pages/decision_grid_config.py`)
   - CRUD interface for decision grid rules
   - Test rule matching with sample data
   - Import/export decision configurations

### **B. State Management**

Store in `st.session_state`:
- Individual agent responses
- Decision grid applied rule
- Audit history with agent breakdowns

---

## **V. Implementation Phases**

### **Phase 1: Foundation (Week 1)**
- Create agent base classes and interfaces
- Implement decision grid config system
- Set up orchestrator skeleton
- Define all Pydantic schemas

### **Phase 2: Specialized Agents (Week 2)**
- Implement Photo Agent (most complex)
- Implement Title Agent
- Implement Specs Agent
- Unit test each agent independently

### **Phase 3: Master Agent & Integration (Week 3)**
- Implement Master Agent with decision grid
- Complete orchestrator with parallel execution
- Create new API endpoints
- Integration testing

### **Phase 4: Frontend & Polish (Week 4)**
- Update Streamlit UI
- Add agent detail views
- Build admin configuration interface
- End-to-end testing
- Documentation updates

---

## **VI. Key Technical Considerations**

### **A. Parallelization Strategy**
- Use `asyncio.gather()` to run Photo, Title, Specs agents concurrently
- Implement timeout mechanisms for each agent
- Handle partial failures gracefully (e.g., if Photo agent fails, continue with Title/Specs)

### **B. LLM Provider Flexibility**
- Abstract agent LLM calls behind provider interface
- Photo Agent: Use vision-capable model (Gemini Pro Vision)
- Title/Specs Agents: Can use lighter model (Gemini Flash)
- Master Agent: Potentially rule-based with minimal LLM calls, or use Gemini Nano/Flash

### **C. Caching & Performance**
- Cache category reference data (relevant/irrelevant titles/photos)
- Consider caching OCR results for same images
- Use FastAPI's background tasks for async processing if needed

### **D. Observability**
- Log each agent's execution time
- Track decision grid rule matches
- Store complete agent outputs for audit trails

### **E. Error Handling Hierarchy**
```
Agent Failure → Use cached/default response → Flag for Master
Master evaluates with "incomplete data" flag
Decision Grid includes rules for incomplete information
```

---

## **VII. Configuration Management**

Update `.env` with:
```
# Multi-Agent Configuration
PHOTO_AGENT_MODEL=gemini-pro-vision
TITLE_AGENT_MODEL=gemini-flash
SPECS_AGENT_MODEL=gemini-flash
MASTER_AGENT_MODEL=gemini-flash
DECISION_GRID_PATH=config/decision_grid.json
AGENT_TIMEOUT_SECONDS=30
ENABLE_AGENT_CACHING=true
```

---

## **VIII. Migration Strategy**

1. **Parallel Running**
   - Keep existing single-LLM auditor active
   - Run multi-agent system alongside
   - Compare results and tune decision grid

2. **Gradual Rollout**
   - A/B test on subset of products
   - Monitor accuracy and latency
   - Iterate on decision grid rules

3. **Full Transition**
   - Deprecate old endpoint
   - Update all frontend calls
   - Archive old auditor code

---

## **IX. Success Metrics**

- **Accuracy**: Comparison with ground truth labels
- **Latency**: Total audit time vs. single-LLM approach
- **Cost**: LLM API costs (may reduce with smaller models per agent)
- **Explainability**: User satisfaction with transparent agent reasoning
- **Maintenance**: Ease of updating decision grid vs. reprompting single LLM

---

This modular plan respects your existing architecture while cleanly introducing the multi-agent pattern. The decision grid approach keeps the Master Agent lightweight and makes the system highly configurable without code changes.