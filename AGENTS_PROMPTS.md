# Multi-Agent Auditor - Agents & Prompts

This document provides a detailed overview of the agents involved in the Multi-Agent Auditor system, their responsibilities, execution order, dependencies, and the specific prompts they use.

## 1. Orchestration Overview

The audit process is managed by the `MultiAgentOrchestrator` (`app/services/multi_agent_orchestrator.py`). It follows a phased execution model to optimize speed and cost while ensuring logical consistency.

### Execution Flow & Dependencies

1.  **Phase 1: Parallel Base Analysis**
    *   **Agents**: `PhotoAgent`, `TitleAgent`, `SpecsAgent`.
    *   **Logic**: These agents run in parallel as they primarily analyze the input data (image, title, specs) independently.
2.  **Phase 2: Conditional Category Verification**
    *   **Agent**: `CategoryAgent`.
    *   **Dependency**: Phase 1 results.
    *   **Condition**: Runs only if no major outliers are detected in Phase 1.
    *   **Context**: Injects `PhotoAgent` visual analysis and OCR results.
3.  **Phase 3: Root Cause Analysis (RCA)**
    *   **Agent**: `RCAAgent`.
    *   **Dependency**: All previous agent results (`Photo`, `Title`, `Specs`, and `Category` if available).
4.  **Phase 4: Final Decision & Recommendations**
    *   **Agent**: `MasterAgent`.
    *   **Dependency**: `RCAAgent` results.
    *   **Logic**: Maps RCA findings to a 32-row decision grid (Truth Table) and generates a seller-facing recommendation.

---

## 2. Agent Details & Prompts

### 2.1. PhotoAgent
*   **Purpose**: Analyzes the product image for visual attributes, OCR text, specifications, and quality issues (outliers).
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
Instructions:
  Task 1:
    Image Analysis: 
    a) Detect the primary object from Product Photo.
    b) Provide a detailed textual description of the product as seen in the photo, focusing on visual attributes, state, and functionality.

  Task 2:
    OCR (Optical Character Recognition): Carefully Extract text from the Product Photo.

 Task 3: 
   Photo Specifications: Extract specifications strictly and only from the Product Photo. If a value is not clearly visible, omit it. Do not infer or assume missing attributes.

  Task 4: 
    Image Visibility Assessment: Evaluate if the Product Photo should be flagged as "outlier" based on these criteria.
       a) Severely Cut Off: ≥80% of the product is not visible in the frame (e.g., product is mostly cut off).
       b) Unidentifiable Blur/Pixelation: The photo is extremely blurred, pixelated, or out-of-focus, making the product indecipherable.
       c) Severely Obscured/Blocked: Product is heavily obscured by other objects, very harsh shadows, or extremely poor lighting to the extent that its key features are hidden.
       d) Generally Unclear/Incomplete: The photo is generally unclear or incomplete to the point that the product's identity or purpose cannot be determined.
       e) Human Blocking the Product: Only flag as "outlier" if the photo is a personal selfie, casual portrait, or social media-style shot where a human is the primary subject and the product is either absent or secondary

Return the results in this strict JSON format:
{
  "task_1": {
    "primary_object": "string",
    "photo_description": "string"
  },
  "task_2": {
    "ocr_text": ["string"]
  },
  "task_3": {
    "photo_specifications": {"key": "value"}
  },
  "task_4": {
    "severely_cut_off": { "status": "outlier/not_outlier/can't_say", "reason": "string" },
    "unidentifiable_blur": { "status": "...", "reason": "..." },
    "severely_obscured": { "status": "...", "reason": "..." },
    "generally_unclear": { "status": "...", "reason": "..." },
    "human_blocking_the_product": { "status": "...", "reason": "..." }
  }
}
```

### 2.2. TitleAgent
*   **Purpose**: Assesses the product title for spelling, duplicates, and internal contradictions. Identifies brands/features and constructs a search query.
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
Product Title: {request.product_title}
Product Specifications: {request.product_specs}
Category Name: {request.mcat_name}

Instructions:

Task 1: 
 Product Title Assessment: Evaluate the Product Title text in isolation: 
    a) Spell Error
    b) Duplicate words in Product Title
    c) Contradiction in Product Title (Conflict within the Title text itself)

Task 2:
 Identify well-known brands, models, or recognizable features from the Product Title and Specifications.
 Give 1 line reason for why Popular for each entity identified as popular.

Task 3:
 Query Construction: Combine the entities from Task 2 into a relevant search query. Let's call it a Product Search Query.

Task 4:
 Category Alignment Check: Analyze if the Product Title aligns with the provided Category Name.

Return all output in JSON format matching this schema:
{
  "task_1": {
    "spell_error": { "status": "outlier/not_outlier/can't_say", "reason": "" },
    "duplicate_words": { "status": "outlier/not_outlier/can't_say", "reason": "" },
    "internal_contradiction": { "status": "outlier/not_outlier/can't_say", "reason": "" }
  },
  "task_2": {
    "identified_entities": [
      {
        "entity": "",
        "source": "title/specs",
        "why_popular": ""
      }
    ]
  },
  "task_3": {
    "product_search_query": ""
  },
  "task_4": {
    "title_category_alignment": { "status": "outlier/not_outlier/can't_say", "reason": "" }
  }
}
```

### 2.3. SpecsAgent
*   **Purpose**: Checks specifications for errors, duplicates, and contradictions with the title.
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
Analyze the following product specifications:
"{request.product_specs}"

Cross-reference with Product Title if provided: "{request.product_title}"

Tasks:
1. Spell Check: Identify any spelling errors in the specs.
2. Duplicate Specs: Detect repeated or redundant specification entries.
3. Contradictions: Check for internal contradictions or contradictions with the title.
4. Spec Extraction: Extract key-value pairs of specifications.

Return the results in this strict JSON format:
{
  "spell_errors": ["string"],
  "duplicate_specs": ["string"],
  "contradictions": ["string"],
  "extracted_specs": {"key": "value"}
}
```

### 2.4. CategoryAgent
*   **Purpose**: Validates if the current category is correct and suggests alternatives based on title, specs, and visual analysis.
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
Product Title: {request.product_title}
Product Specifications: {request.product_specs}
Current Category (if any): {request.mcat_name}
Photo Analysis:
- Visual Object: {photo_object}
- Visual Description: {photo_description}
- Detected Text (OCR): {ocr_text}

Instructions:
1. Analyze the product information provided.
2. Determine the most accurate category for this product.
3. If the current category is correct, confirm it.
4. If there is a better category, suggest it.
5. Provide reasoning for your choice.

Return the results in this strict JSON format:
{
  "suggested_category": "string",
  "confidence_score": float (0.0 to 1.0),
  "reasoning": "string",
  "alternative_categories": ["string"]
}
```

### 2.5. RCAAgent
*   **Purpose**: Synthesizes all agent findings to identify root causes and assign severity.
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
You are a Root Cause Analysis (RCA) specialist for product auditing.
Below are the results from various specialized agents that audited a product.

Agent Results:
{context_str}

Instructions:
1. Synthesize all findings.
2. Identify the root cause for any issues (outliers, contradictions, errors).
3. Determine the severity of each issue.
4. Recommend a final verdict (PASS, FAIL, REVIEW).
5. Provide a summary of your analysis.

Return the results in this strict JSON format:
{
  "root_cause_summary": "string",
  "identified_issues": [
    {
      "issue_type": "PHOTO_QUALITY | TITLE_QUALITY | SPECS_QUALITY | TITLE_SPECS_CONTRADICTION | PHOTO_TITLE_CONTRADICTION | PHOTO_SPECS_CONTRADICTION | PHOTO_CATEGORY_MISMATCH | TITLE_CATEGORY_MISMATCH | CATEGORY_MISMATCH | OTHER",
      "severity": "LOW/MEDIUM/HIGH/CRITICAL",
      "description": "string",
      "evidence": "string"
    }
  ],
  "recommended_verdict": "PASS/FAIL/REVIEW",
  "confidence": float (0.0 to 1.0)
}
```

### 2.6. MasterAgent
*   **Purpose**: The final decision maker. It maps RCA issues to 5 binary flags to look up a decision in a truth table and generates a polite recommendation.
*   **Model**: `gemini-1.5-flash`
*   **Primary Logic**: Decision Grid (32-row truth table loaded from `config/decision_grid.json`).

#### Decision Grid Execution Flow
1.  **Extract Facts**: The agent scans the RCA `identified_issues` to determine the state (True/False) of 5 binary flags:
    *   `photo_category`: Mismatch between photo and category.
    *   `title_category`: Mismatch between title and category.
    *   `photo_title`: Contradiction between photo and title.
    *   `photo_specs`: Contradiction between photo and specifications.
    *   `title_specs`: Contradiction between title and specifications.
2.  **Generate Code**: These flags are combined into a 5-digit binary code (e.g., `00100`).
3.  **Lookup Message**: The code is used to look up the specific decision message in `config/decision_grid.json` (e.g., `00100` -> "Review Title & Photo").
4.  **Determine Action**:
    *   Message contains "Rejected" -> **FAIL**
    *   Message is empty -> **PASS**
    *   Otherwise -> **REVIEW**
5.  **Generate Recommendation**: An LLM call generates a polite seller recommendation based on the decision message and specific RCA issues.

*   **Recommendation Prompt**:
```text
You are a polite quality assurance expert. A product listing has been audited and found to have issues.

AUDIT OUTCOME: {decision_text}
SPECIFIC ISSUES FOUND:
{issues_str}

PRODUCT TITLE: {request.product_title}

TASK: Write a polite, reasonable, and helpful recommendation to the seller to help them improve this listing.
- Tone: Suggestive, polite, and logical.
- Length: Strictly no more than 2 lines.
- Focus: Be specific to the errors mentioned (e.g. mismatch between title and photo).

RECOMMENDATION:
```
