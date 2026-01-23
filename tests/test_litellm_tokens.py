import pytest
from unittest.mock import MagicMock, patch
from app.services.litellm_service import LiteLLMService


class MockMessage:
    def __init__(self, content):
        self.content = content


class MockChoice:
    def __init__(self, message):
        self.message = message


class MockUsage:
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


@pytest.mark.asyncio
async def test_litellm_tokens_returned():
    # Arrange
    with patch("app.services.litellm_service.litellm.completion") as mock_completion:
        prompt_tokens = 789
        completion_tokens = 101
        total_tokens = 890

        usage = MockUsage(prompt_tokens, completion_tokens, total_tokens)

        mock_response = MagicMock()
        mock_response.choices = [MockChoice(MockMessage("Test response"))]
        mock_response.usage = usage

        mock_completion.return_value = mock_response

        service = LiteLLMService(model_name="google/gemini-2.5-flash")

        # We assume cost calculation succeeds or fails, doesn't matter for token test
        with patch("app.services.litellm_service.litellm.completion_cost") as mock_cost:
            mock_cost.return_value = 0.0

            # Act
            messages = [{"role": "user", "content": "Hello"}]
            response = await service.chat_with_usage(messages)

            # Assert
            assert "usage" in response
            assert response["usage"]["prompt_tokens"] == prompt_tokens
            assert response["usage"]["completion_tokens"] == completion_tokens
            assert response["usage"]["total_tokens"] == total_tokens
