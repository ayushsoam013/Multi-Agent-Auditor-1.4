# Multi-Agent Auditor - Agents & Prompts

This document provides a detailed overview of the agents involved in the Multi-Agent Auditor system, their responsibilities, execution order, dependencies, and the specific prompts they use.

## 1. Orchestration Overview

The audit process is managed by the `MultiAgentOrchestrator` (`app/services/multi_agent_orchestrator.py`). It follows a sequential and conditional execution model to ensure logical consistency and efficiency.

### Execution Flow & Dependencies

1.  **Step 1: Visual Analysis**
    *   **Agent**: `PhotoAgent`
    *   **Logic**: Analyzes the product image for visual attributes, OCR text, photo specifications, and quality issues.
    *   **Output**: Used by `TextualAgent`, `CategoryAgent`, and `RCAAgent`.

2.  **Step 2: Textual & Cross-Modal Analysis**
    *   **Agent**: `TextualAgent`
    *   **Dependency**: `PhotoAgent` results.
    *   **Logic**: Audits Title and Specifications for internal quality. Performs cross-modal consistency checks (e.g., Title vs. Photo, Specs vs. Photo).

3.  **Step 3: Conditional Category Verification**
    *   **Agent**: `CategoryAgent`
    *   **Dependency**: `PhotoAgent` and `TextualAgent` results.
    *   **Condition**: Runs only if **NO** major outliers are detected in the Photo or Textual phases.
    *   **Logic**: Validates if the product belongs to the assigned category using visual and textual clues.

4.  **Step 4: Root Cause Analysis (RCA)**
    *   **Agent**: `RCAAgent`
    *   **Dependency**: All previous agent results (`Photo`, `Textual`, and `Category` if available).
    *   **Logic**: Synthesizes all findings to identify the root cause of issues and assigns severity.

5.  **Step 5: Final Decision & Recommendations**
    *   **Agent**: `MasterAgent`
    *   **Dependency**: `RCAAgent` results.
    *   **Logic**: Maps RCA findings to a Decision Grid (Truth Table) to determine the verdict (PASS/FAIL/REVIEW) and generates a seller-facing recommendation.

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

### 2.2. TextualAgent
*   **Purpose**: Audits product textual information (Title, Specs) and checks consistency with Photo and Category. Combines functionalities of previous Title and Specs agents.
*   **Model**: `gemini-1.5-flash`
*   **Prompt**:
```text
Product Title: {request.product_title}
Product Specifications: {request.product_specs}
Category Name: {request.mcat_name}
Photo Agent Output (Textual Only):
{photo_output_str}


Instructions:

Task 1: 
 Product Title Assessment (Internal Only) : Evaluate the Product Title text in isolation: 
	a) Spell Error
b) Duplicate words in Product Title
c) Contradiction in Product Title 
(Conflict within the Title text itself)

  Task 2: 
 Product Specifications Assessment (Internal Only):  Evaluate the Product Specifications text in isolation: 
a) Spell Error 
b) Duplicate Specifications 
c) Internal Contradiction 
(Conflict within the Specifications text itself)

  Task 3:
 Identify well-known brands, models, or recognizable features from:
- Primary Object
- OCR text from Input
- Product Title
- Product Specifications
- Photo Specifications
 Give 1 line reason for why Popular for each entity identified as popular.

  Task 4:
    Query Construction: Combine the entities from Task 3  into a relevant search query. Let's call it a Product Search Query.

  Task 5: 
    Identify if there is contradiction in:
Analyze each pair independently. An "outlier" here requires a mismatch between the two listed sources. If the sources agree on the core fact, it is "not outlier," even if one source is poorly formatted or has internal errors.
      a) Primary Object of Product Photo- Title
      b) Primary Object of Product Photo - Product Specifications
      c) Product Title - Product Specifications 
      d) Within the Product Search Query
     e) Photo Description ↔ Product Title
     f) Photo Specifications ↔ Product Specifications

    Task 6:
Category Analysis: Analyze the Category : "Category Name"  and identify the type of products it represents.
Only flag as "outlier" if the entity does not belong in the category. Ignore spelling/formatting errors in the entities. Use the Category understanding from above to identify if there is a contradiction in:
      a) Primary Object ↔ Category
      b) Photo Description ↔ Category
      c) Product Search Query - Category Name
      d) Product title - Category Name

  Task 7:
Core Alignment Check : Verify if the product's primary function and operating mechanism match the category's fundamental definition. Flag as outlier if:
Mechanism Mismatch: The product operates differently than the category implies (e.g., manual vs. electric, stovetop vs. automatic).
Entity Mismatch: The product is a toy, model, accessory, or spare part, while the category represents the functional standalone item.
Visual Mimicry: The product is designed to look like the category item but lacks its core utility (e.g., a camera-shaped lighter).

Give all output in JSON format.
Give response for task and subtasks of task 1,  task 2, task 5, task 6 and task 7 as outlier / not outlier / can't say for each subtask. Give one reason for each subtask of task 1,  task 2, task 5, task 6 and task 7.


{
  "task_1": {
    "spell_error": { "status": "", "reason": "" },
    "duplicate_words": { "status": "", "reason": "" },
    "internal_contradiction": { "status": "", "reason": "" }
  },
  "task_2": {
    "spell_error": { "status": "", "reason": "" },
    "duplicate_specifications": { "status": "", "reason": "" },
    "internal_contradiction": { "status": "", "reason": "" }
  },
  "task_3": {
    "identified_entities": [
      {
        "entity": "",
        "source": "",
        "why_popular": ""
      }
    ]
  },
  "task_4": {
    "product_search_query": ""
  },
  "task_5": {
    "photo_title": { "status": "", "reason": "" },
    "photo_specs": { "status": "", "reason": "" },
    "title_specs": { "status": "", "reason": "" },
    "query_internal": { "status": "", "reason": "" },
    "photo_description_title": { "status": "", "reason": "" },
    "photo_specs_specs": { "status": "", "reason": "" }
  },
  "task_6": {
    "primary_object_category": { "status": "", "reason": "" },
    "photo_description_category": { "status": "", "reason": "" },
    "query_category": { "status": "", "reason": "" },
    "title_category": { "status": "", "reason": "" }
  },
  "task_7": {
    "mechanism_mismatch": { "status": "", "reason": "" },
    "entity_mismatch": { "status": "", "reason": "" },
    "visual_mimicry": { "status": "", "reason": "" }
  }
}
```

### 2.3. CategoryAgent
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

### 2.4. RCAAgent
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

### 2.5. MasterAgent
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
