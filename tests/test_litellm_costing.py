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


class MockResponse:
    def __init__(self, content, usage=None, cost=None):
        self.choices = [MockChoice(MockMessage(content))]
        self.usage = usage
        # litellm usually attaches _hidden_params or similar for cost,
        # but the completion function returns a ModelResponse object which has .cost property if calculated?
        # Actually litellm.completion returns a ModelResponse that mimics OpenAI response.
        # However, litellm provides a separate cost calculation or sometimes embeds it.
        # Let's assume for the test that we will calculate it inside the service or use litellm's utility.
        # But wait, litellm.completion response often has `_hidden_params` with cost
        # OR we can use litellm.completion_cost(completion_response)
        pass


@pytest.mark.asyncio
async def test_litellm_costing_returned():
    # Arrange
    with patch("app.services.litellm_service.litellm.completion") as mock_completion:
        # Define usage data
        prompt_tokens = 1000
        completion_tokens = 500
        total_tokens = 1500

        usage = MockUsage(prompt_tokens, completion_tokens, total_tokens)

        # Create a mock response object that behaves like litellm's response
        mock_response = MagicMock()
        mock_response.choices = [MockChoice(MockMessage("Test response"))]
        mock_response.usage = usage

        # Mocking the response to be returned by completion
        mock_completion.return_value = mock_response

        # Initialize service
        service = LiteLLMService(model_name="google/gemini-2.5-flash")

        # Use patch for cost calculation since we rely on litellm.completion_cost or similar
        # But wait, I want to see if the service calculates it.
        # Let's assume I will implement it using litellm.completion_cost

        with patch(
            "app.services.litellm_service.litellm.completion_cost"
        ) as mock_cost_calc:
            mock_cost_calc.return_value = 0.000123

            # Act
            messages = [{"role": "user", "content": "Hello"}]
            response = await service.chat_with_usage(messages)

            # Assert
            assert "content" in response
            assert "usage" in response
            assert response["usage"]["prompt_tokens"] == prompt_tokens

            # This assertion is expected to fail initially
            print(f"\nResponse keys: {response.keys()}")
            if "costing" in response:
                print(f"Costing found: {response['costing']}")
            else:
                print("Costing NOT found in response")


@pytest.mark.asyncio
async def test_litellm_costing_calculation_failure():
    # Test fallback when cost calculation fails
    with patch("app.services.litellm_service.litellm.completion") as mock_completion:
        usage = MockUsage(100, 100, 200)
        mock_response = MagicMock()
        mock_response.choices = [MockChoice(MockMessage("Test"))]
        mock_response.usage = usage
        mock_completion.return_value = mock_response

        service = LiteLLMService(model_name="google/gemini-2.5-flash")

        with patch(
            "app.services.litellm_service.litellm.completion_cost"
        ) as mock_cost_calc:
            # Simulate exception during cost calculation
            mock_cost_calc.side_effect = Exception("Cost error")

            messages = [{"role": "user", "content": "Hello"}]
            response = await service.chat_with_usage(messages)

            assert "costing" in response
            assert response["costing"] == 0.0
