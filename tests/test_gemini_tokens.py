import pytest
from unittest.mock import MagicMock, patch
from app.services.gemini_gen_service import GeminiGenService


class MockUsageMetadata:
    def __init__(self, prompt_tokens, candidates_tokens, total_tokens):
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = candidates_tokens
        self.total_token_count = total_tokens


class MockResponse:
    def __init__(self, text, usage_metadata=None):
        self.text = text
        self.usage_metadata = usage_metadata


@pytest.mark.asyncio
async def test_gemini_tokens_returned():
    # Arrange
    with patch("app.services.gemini_gen_service.genai.Client") as MockClient:
        mock_instance = MockClient.return_value
        mock_models = mock_instance.models

        prompt_tokens = 123
        completion_tokens = 456
        total_tokens = 579

        usage = MockUsageMetadata(prompt_tokens, completion_tokens, total_tokens)
        mock_response = MockResponse("Test response", usage)

        mock_models.generate_content.return_value = mock_response

        service = GeminiGenService(model_name="gemini-1.5-flash")

        # Act
        messages = [{"role": "user", "content": "Hello"}]
        response = await service.chat_with_usage(messages)

        # Assert
        assert "usage" in response
        assert response["usage"]["prompt_tokens"] == prompt_tokens
        assert response["usage"]["completion_tokens"] == completion_tokens
        assert response["usage"]["total_tokens"] == total_tokens
