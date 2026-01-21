# Multi-Agent Audit Flow: Detailed Walkthrough

This document provides a comprehensive technical walkthrough of the agent orchestration flow, class structures, prompting mechanisms, and data schemas used in the Multi-Agent Auditor application, specifically focusing on the `/multi-agent` endpoint.

---

## **1. Entry Point: `/multi-agent` Endpoint**

**File:** [audit.py](file:///c:/Users/Imart/Documents/POC/Multi-Agent-Auditor-1.4/app/api/v1/endpoints/audit.py)

The process begins when a user submits a product for auditing (image, title, specs, and category name).

- **Input Handling:** The endpoint receives multipart form data, saves the uploaded image to a temporary directory (`temp_uploads/`), and initializes an `AgentRequest` object.
- **Orchestration Trigger:** It calls `orchestrator.run_audit(request)`, which is the main entry point for the agentic logic.

---

## **2. Orchestration Logic**

**File:** [multi_agent_orchestrator.py](file:///c:/Users/Imart/Documents/POC/Multi-Agent-Auditor-1.4/app/services/multi_agent_orchestrator.py)

The `MultiAgentOrchestrator` manages the lifecycle and execution order of specialized agents.

### **Execution Flow:**

1. **Parallel Execution (Stage 1):** `PhotoAgent` and `SpecsAgent` are executed concurrently using `asyncio.gather()`.
2. **Context Enrichment:** The analysis result from `PhotoAgent` (detected objects, OCR text, photo specs) is injected into the `request.context`.
3. **Sequential Execution (Stage 2):** `TitleAgent` is then called. It uses the enriched context from `PhotoAgent` to perform cross-validation (e.g., checking if the title matches what's actually in the photo).
4. **Aggregation:** All specialized results are gathered into `request.context["agent_results"]`.
5. **Final Decision (Stage 3):** `MasterAgent` reviews all findings, applies decision grid rules, and generates the final audit summary and search query.

---

## **3. Agent Architecture & Classes**

**Directory:** [agents/](file:///c:/Users/Imart/Documents/POC/Multi-Agent-Auditor-1.4/app/services/agents/)

### **The Base Class: `BaseAgent`**

All agents inherit from `BaseAgent`, which provides:

- **`__init__`**: Standardizes agent names, model selection (`gemini-1.5-flash` by default), and response classes.
- **`process()`**: A wrapper that handles performance timing, error logging, and calls the abstract `_process_logic()`.

## **4. Detailed Agent Profiles**

Each agent is a subclass of `BaseAgent` and implements its own `_process_logic`.

### **A. PhotoAgent**

- **Class:** `PhotoAgent` (in `photo_agent.py`)
- **Primary Model:** `gemini-1.5-flash`
- **Tasks:**
  - **Task 1: Image Analysis** - Detects primary objects and provides textual descriptions.
  - **Task 2: OCR** - Extracts visible text from the image.
  - **Task 3: Photo Specs** - Extracts technical specifications visible ONLY in the photo.
  - **Task 4: Visibility Assessment** - Flags "outliers" based on blur, cut-off, or obstruction.
- **Prompt Injection:** Combines task instructions with the image bytes and text prompts into a single multimodal request.
- **Pydantic Schema:** `PhotoAgentResponse` containing `PhotoAnalysisResult`.

### **B. SpecsAgent**

- **Class:** `SpecsAgent` (in `specs_agent.py`)
- **Primary Model:** `gemini-1.5-flash`
- **Tasks:**
  - Spell checking of specification text.
  - Detection of duplicate specifications.
  - Identification of internal contradictions.
  - Extraction of key-value pairs from text.
- **Prompt Injection:** Simple text prompt injecting `request.product_specs` and `request.product_title`.
- **Pydantic Schema:** `SpecsAgentResponse` containing `SpecsAnalysisResult`.

### **C. TitleAgent**

- **Class:** `TitleAgent` (in `title_agent.py`)
- **Primary Model:** `gemini-1.5-flash`
- **Role:** Performs high-level cross-validation between text and visual data.
- **Tasks:**
  - Validates title/specs for internal errors (spelling, duplicates).
  - Identifies popular brands/entities from all sources.
  - Constructs a "Product Search Query".
  - **Task 5 & 6:** Checks for contradictions between Photo ↔ Title, Photo ↔ Specs, Title ↔ Category, etc.
- **Prompt Injection:** Injects `product_title`, `product_specs`, `mcat_name`, AND a JSON-stringified version of the `PhotoAgent` output from the context.
- **Pydantic Schema:** `TitleAgentResponse` containing `TitleAnalysisResult`.

### **D. MasterAgent**

- **Class:** `MasterAgent` (in `master_agent.py`)
- **Primary Model:** `gemini-1.5-flash` (plus local Decision Grid logic)
- **Role:** Final aggregator and decision maker.
- **Logic:**
  1. Performs cross-validation analytics on results from Photo, Title, and Specs agents.
  2. Extracts "facts" (e.g., `photo_quality_error: True`).
  3. Uses `DecisionGridLoader` to match these facts against a rule set (`config/decision_grid.json`) to get an initial `PASS/FAIL/REVIEW` action.
  4. Calls the LLM to synthesize all findings into a final summary and search query.
- **Pydantic Schema:** `MasterAgentResponse` containing `CrossValidation`, `FinalErrors`, and `audit_decision`.

---

## **5. Prompt Injection & LLM Interaction**

### **How Prompts are Constructed:**

Prompts are defined within each agent's `_process_logic` or a dedicated `_get_prompt` method. They are dynamically constructed using Python f-strings to inject:

- **User Input:** Title, specs, and category name from the initial request.
- **Context:** Previous agent outputs (e.g., `TitleAgent` receives `PhotoAgent`'s output via context).
- **Instructions:** Strict task-based instructions and formatting rules.

### **System vs. User Prompts:**

In the current implementation, most agents use a single `user` message containing the full set of instructions and data. This ensures the model treats the specific audit tasks as the primary objective for that turn.

### **Structured Output:**

All agents use `response_mime_type: "application/json"` in the LLM configuration. This forces the Gemini model to return valid JSON, which is then parsed and validated against Pydantic models.

---

## **6. Pydantic Schemas**

**File:** [agent_schemas.py](file:///c:/Users/Imart/Documents/POC/Multi-Agent-Auditor-1.4/app/schemas/agent_schemas.py)

The system relies heavily on Pydantic for "Type Safety" between the LLM and the application.

| Schema                  | Purpose                                                                                |
| :---------------------- | :------------------------------------------------------------------------------------- |
| `AgentRequest`          | The universal input object containing title, specs, image info, and shared context.    |
| `BaseAgentResponse`     | Common fields like `agent_name`, `status`, and `processing_time`.                      |
| `PhotoAgentResponse`    | Extends base with `PhotoAnalysisResult` (Tasks 1-4).                                   |
| `TitleAgentResponse`    | Extends base with `TitleAnalysisResult` (Tasks 1-7).                                   |
| `MasterAgentResponse`   | Includes the final decision, reasoning, and cross-validation flags.                    |
| `MultiAgentAuditResult` | The top-level response returned to the API, containing all individual agent responses. |

---

## **7. Saving and Persistence**

- **In-Memory Context:** The `AgentRequest.context` dictionary persists data during a single audit lifecycle, allowing agents to share information.
- **File System:** Images are saved to `temp_uploads/` for processing.
- **Service Persistence:** Agents themselves are stateless; they are instantiated once by the `MultiAgentOrchestrator` and reused across requests.
- **Audits:** Currently, full audit logs are returned to the user but not saved to a primary database (SQL/NoSQL) in this version of the backend.

---

## **8. Testing & Verification**

**Script:** [test_multi_agent.py](file:///c:/Users/Imart/Documents/POC/Multi-Agent-Auditor-1.4/test_multi_agent.py)

You can verify the entire multi-agent flow by running the provided testing script. This script:

1.  Picks a random product title, specs, and category.
2.  Uses a sample image (e.g., `misc/sofa.jpg`).
3.  Sends a `POST` request to the `/multi-agent` endpoint.
4.  Prints the status code and the comprehensive JSON response from all agents.

**Command to run:**

```powershell
python test_multi_agent.py
```

---
