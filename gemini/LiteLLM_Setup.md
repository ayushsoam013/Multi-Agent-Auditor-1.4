# Gemini Client Setup & Usage Guide

This document details the configuration, valid usage, and future maintenance instructions for the LLM Setup module. This module provides a client wrapper for interacting with the Gemini 2.5 Flash model via an OpenAI-compatible gateway.

## 1. Overview

The `gemini_client.py` script initializes a client that handles:

- **Resiliency**: Basic error handling for API connection issues and JSON parsing.

## 2. Prerequisites

### Environment Variables

The application relies on `python-dotenv` to load configuration details. Ensure your `.env` file in the project root contains the following key:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

### Python Dependencies

The following libraries are required. They should be included in your `requirements.txt`:

- `openai`: To communicate with the custom gateway using the OpenAI protocol.
- `python-dotenv`: To load environment variables.
- `requests`: For HTTP requests (used in internal helper methods).

Installation command:

```bash
pip install openai python-dotenv requests
```

## 3. Implementation Details

### Configuration Constants

- **BASE_URL**: `https://imllm.intermesh.net/v1` - This points to the custom internal gateway.
- **MODEL_NAME**: `google/gemini-2.5-flash` - The specific model version being targeted.
- **TIMEOUT**: `120.0` seconds - Timeout setting for the API calls.

### The `LLMClient` Class

## 4. Usage Guide

### Importing the Client

The module exports a pre-initialized instance named `gemini_client`.

```python
from backend.gemini_client import gemini_client
```

## 5. Future Setup & Maintenance

### Changing the Model

To switch to a newer version of Gemini or a different model supported by the gateway, update the `MODEL_NAME` constant at the top of the file:

```python
MODEL_NAME = "google/gemini-pro-1.5" # Example
```

```

```

### Adding New Functionalities

To add new capabilities (e.g., text summarization or captioning):

1. Add a new method to `LLMClient` (e.g., `generate_caption(self, text, image_bytes)`).
2. Construct a new `messages` payload appropriate for the task.
3. Call `client.chat.completions.create` with your new prompt.
