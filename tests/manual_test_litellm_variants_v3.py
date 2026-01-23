
import litellm
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LITELLM_API_KEY")
api_base = "https://imllm.intermesh.net/v1"

def test_model(model_name, custom_provider=None):
    print(f"\nTesting Model: {model_name} | Provider: {custom_provider}")
    try:
        response = litellm.completion(
            model=model_name,
            messages=[{"role": "user", "content": "hello"}],
            api_base=api_base,
            api_key=api_key,
            timeout=10,
        )
        print(f"SUCCESS! Response: {response.choices[0].message.content[:50]}...")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Test with custom_llm_provider="openai"
    test_model("litellm_proxy/google/gemini-2.5-flash")
    test_model("litellm_proxy/google/gemini-2.0-flash")
