# Multi-Agent Audit Flow: Detailed Walkthrough

This document provides a comprehensive technical walkthrough of the agent orchestration flow, class structures, prompting mechanisms, and data schemas used in the Multi-Agent Auditor application.

---

## **1. Entry Point: `/multi-agent` Endpoint**

**File:** `app/api/v1/endpoints/audit.py`

The process begins when a user submits a product for auditing (image, title, specs, and category name).

- **Input Handling:** The endpoint receives multipart form data, saves the uploaded image to a temporary directory (`temp_uploads/`), and initializes an `AgentRequest` object.
- **Orchestration Trigger:** It calls `orchestrator.run_audit(request)`, which is the main entry point for the agentic logic.

---

## **2. Orchestration Logic**

**File:** `app/services/multi_agent_orchestrator.py`

The `MultiAgentOrchestrator` manages the lifecycle and execution order of specialized agents.

### **Execution Flow:**

1.  **Step 1: Visual Analysis (PhotoAgent)**
    *   **Agent**: `PhotoAgent`
    *   **Action**: Analyzes the product image for visual attributes, OCR text, and quality issues.
    *   **Output**: Results are stored and injected into the context for subsequent agents.

2.  **Step 2: Textual & Cross-Modal Analysis (TextualAgent)**
    *   **Agent**: `TextualAgent`
    *   **Dependency**: Requires `PhotoAgent` output.
    *   **Action**: Audits Title and Specs for internal quality and checks for contradictions with the Photo (e.g., "Photo shows a Chair, Title says Table").

3.  **Step 3: Category Verification (CategoryAgent) - Conditional**
    *   **Agent**: `CategoryAgent`
    *   **Condition**: Only executed if `PhotoAgent` and `TextualAgent` do not detect critical "outliers".
    *   **Action**: Ensures the product is mapped to the most accurate category (MCAT) based on combined visual and textual evidence.

4.  **Step 4: Root Cause Analysis (RCAAgent)**
    *   **Agent**: `RCAAgent`
    *   **Action**: Synthesizes all findings from Photo, Textual, and (if applicable) Category agents to identify the root cause of issues and assign severity.

5.  **Step 5: Final Decision (MasterAgent)**
    *   **Agent**: `MasterAgent`
    *   **Action**: Maps RCA findings to a Decision Grid (Truth Table) to determine the verdict (PASS/FAIL/REVIEW) and generates a seller-facing recommendation.

---

## **3. Agent Architecture & Classes**

**Directory:** `app/services/agents/`

### **The Base Class: `BaseAgent`**

All agents inherit from `BaseAgent`, which provides:

- **`__init__`**: Standardizes agent names, model selection (`gemini-1.5-flash` by default), and response classes.
- **`process()`**: A wrapper that handles performance timing, error logging, and calls the abstract `_process_logic()`.

## **4. Detailed Agent Profiles**

### **A. PhotoAgent**

- **Class:** `PhotoAgent` (in `photo_agent.py`)
- **Tasks:**
  - **Task 1: Image Analysis** - Detects primary objects and provides textual descriptions.
  - **Task 2: OCR** - Extracts visible text from the image.
  - **Task 3: Photo Specs** - Extracts technical specifications visible ONLY in the photo.
  - **Task 4: Visibility Assessment** - Flags "outliers" based on blur, cut-off, or obstruction.
- **Pydantic Schema:** `PhotoAgentResponse` containing `PhotoAnalysisResult`.

### **B. TextualAgent**

- **Class:** `TextualAgent` (in `textual_agent.py`)
- **Role:** Comprehensive textual and cross-modal auditor.
- **Tasks:**
  - **Task 1 & 2:** Title and Specs internal assessment (spelling, duplicates, internal contradictions).
  - **Task 3:** Entity identification (brands, models).
  - **Task 4:** Search Query Construction.
  - **Task 5:** Cross-Modal Verification (Photo vs. Title, Photo vs. Specs, etc.).
  - **Task 6 & 7:** Category alignment and core functional checks.
- **Pydantic Schema:** `TextualAgentResponse` containing `TextualAnalysisResult`.

### **C. CategoryAgent**

- **Class:** `CategoryAgent` (in `category_agent.py`)
- **Role:** Specialized for category verification (MCAT alignment).
- **Tasks:**
  - **Task 1: Cross-modal Category Check** - Validates if the product's category matches its visual and textual features.
  - **Task 2: MCAT Recommendation** - Suggests the optimal category and provides a confidence score.
- **Pydantic Schema:** `CategoryAgentResponse` containing `CategoryAnalysisResult`.

### **D. RCAAgent**

- **Class:** `RCAAgent` (in `rca_agent.py`)
- **Role:** Root Cause Analysis synthesizer.
- **Logic:** Aggregates all agent outputs to pinpoint specific issues (e.g., "PHOTO_TITLE_CONTRADICTION") and assigns severity.
- **Pydantic Schema:** `RCAAgentResponse`.

### **E. MasterAgent**

- **Class:** `MasterAgent` (in `master_agent.py`)
- **Role:** Final decision maker.
- **Logic:**
  1.  Extracts binary flags from `RCAAgent` results.
  2.  Lookups the decision in the `DecisionGrid` (CSV truth table).
  3.  Generates a polite recommendation string.
- **Pydantic Schema:** `MasterAgentResponse`.

---

## **5. Pydantic Schemas**

**File:** `app/schemas/agent_schemas.py`

The system relies heavily on Pydantic for "Type Safety" between the LLM and the application.

| Schema                  | Purpose                                                                                |
| :---------------------- | :------------------------------------------------------------------------------------- |
| `AgentRequest`          | The universal input object containing title, specs, image info, and shared context.    |
| `BaseAgentResponse`     | Common fields like `agent_name`, `status`, and `processing_time`.                      |
| `PhotoAgentResponse`    | Extends base with `PhotoAnalysisResult`.                                               |
| `TextualAgentResponse`  | Extends base with `TextualAnalysisResult`.                                             |
| `CategoryAgentResponse` | Extends base with `CategoryAnalysisResult`.                                            |
| `RCAAgentResponse`      | Extends base with `RCAAnalysisResult`.                                                 |
| `MasterAgentResponse`   | Includes the final decision, reasoning, and cross-validation flags.                    |
| `MultiAgentAuditResult` | The top-level response returned to the API, containing all individual agent responses. |

---

## **6. Testing & Verification**

**Script:** `test_multi_agent.py`

You can verify the entire multi-agent flow by running the provided testing script:

```powershell
python test_multi_agent.py
```
