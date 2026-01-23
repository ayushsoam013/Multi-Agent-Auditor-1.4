# Multi-Agent Auditor System - Architecture Reference

## **I. High-Level Architecture**

### **Agent Hierarchy**

```
Input (Product Data + Context)
    ↓
┌─────────────────────────────────────┐
│   Phase 1: Visual Analysis          │
│   - Photo Agent (Vision + OCR)      │
└─────────────────────────────────────┘
    ↓ (Visual Context)
┌─────────────────────────────────────┐
│   Phase 2: Textual Analysis         │
│   - Textual Agent                   │
│     (Title, Specs, Cross-Modal)     │
└─────────────────────────────────────┘
    ↓ (If No Outliers)
┌─────────────────────────────────────┐
│   Phase 3: Category Verification    │
│   - Category Agent                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Phase 4: Synthesis & Decision     │
│   - RCA Agent (Root Cause Analysis) │
│   - Master Agent (Decision Grid)    │
└─────────────────────────────────────┘
    ↓
Final Audit Result
```

---

## **II. Agent Responsibilities Breakdown**

### **1. Photo Agent**
**Role:** The "Eyes" of the system.
**Input:** Product Photo.
**Processing:**
- Primary object detection & description.
- OCR extraction (reading text on the box/product).
- Visibility assessment (blur, cut-off, obstruction).
**Output:** Structured JSON with visual description and OCR text.

### **2. Textual Agent**
**Role:** The "Auditor".
**Input:** Product Title, Specs, Category Name + **Photo Agent Output**.
**Processing:**
- **Internal Checks:** Spelling, duplicates, internal contradictions in Title/Specs.
- **Cross-Modal Checks:** Does the Title match the Photo? Do Specs match the Photo?
- **Searchability:** Constructs a valid search query.
- **Category Checks:** Does the product fit the category definition?
**Output:** Detailed breakdown of textual and cross-modal consistency.

### **3. Category Agent (Conditional)**
**Role:** The "Classifier".
**Input:** Title, Specs, Photo Context, Current Category.
**Processing:**
- Validates if the assigned category (MCAT) is correct.
- Suggests alternative categories if the current one is wrong.
**Condition:** Only runs if Photo and Textual agents found no "blocker" issues (outliers).

### **4. RCA Agent**
**Role:** The "Analyst".
**Input:** Outputs from all previous agents.
**Processing:**
- Synthesizes all findings into a coherent narrative.
- Identifies the *Root Cause* of any failure.
- Assigns severity (Low/Medium/High/Critical).

### **5. Master Agent**
**Role:** The "Judge".
**Input:** RCA Report.
**Processing:**
- **Fact Extraction:** Converts RCA issues into 5 binary flags (e.g., `photo_title_contradiction = True`).
- **Decision Grid Lookup:** Consults the `decision_grid.csv` truth table to find the binding verdict.
- **Recommendation:** Generates a polite, constructive message for the seller.

---

## **III. Backend Implementation Strategy**

### **A. Service Layer Architecture** (`app/services/`)

1. **`multi_agent_orchestrator.py`**
   - Coordinates the sequential/conditional flow.
   - Manages data passing (`context`) between agents.

2. **`agents/` Directory**
   - Contains individual agent classes inheriting from `BaseAgent`.
   - `photo_agent.py`, `textual_agent.py`, `category_agent.py`, `rca_agent.py`, `master_agent.py`.

### **B. Decision Grid Design**

The decision logic is decoupled from the code and stored in `config/decision_grid.json` (loaded from a CSV).

- **Input:** 5 Boolean Flags.
- **Output:** Decision Code + Action (PASS/FAIL/REVIEW).
- **Benefit:** Business rules can be updated without changing Python code.

---

## **IV. Data Models** (`app/schemas/`)

Pydantic models ensure type safety across the pipeline:

1. **`AgentRequest`**: Universal input.
2. **`PhotoAgentResponse`**: Visual analysis results.
3. **`TextualAgentResponse`**: Text & cross-modal results.
4. **`CategoryAgentResponse`**: Category validation results.
5. **`RCAAgentResponse`**: Root cause synthesis.
6. **`MasterAgentResponse`**: Final verdict and recommendation.

---

## **V. Key Technical Considerations**

### **A. Conditional Execution**
To save costs and time, the **Category Agent** is skipped if the product is already determined to be an "Outlier" (e.g., blurry photo or gibberish title) by the upstream agents.

### **B. Context Propagation**
The `PhotoAgent` runs first so that its visual insights (e.g., "This is a red chair") are available to the `TextualAgent` when it checks if the title ("Blue Table") is accurate.

### **C. Deterministic Decision Making**
The final verdict is **not** decided by an LLM prompt ("Is this good?"). It is decided by a rigid Truth Table based on the factual findings of the agents. This prevents LLM "mood swings" from affecting compliance standards.
