import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def test_chat_completions(provider, model=None, system_prompt="You are a helpful assistant.", user_prompt="Hello, who are you?"):
    print(f"\n--- Testing Provider: {provider} | Model: {model or 'default'} ---")
    
    url = f"{API_BASE}/chat/completions"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    payload = {
        "messages": messages,
        "provider": provider,
        "model": model,
        "temperature": 0.5,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Content: {data.get('content')[:100]}...")
            print(f"Model Used: {data.get('model')}")
            print(f"Usage: {json.dumps(data.get('usage'), indent=2)}")
            
            # Basic validation
            assert "content" in data
            assert "model" in data
            if data.get("usage"):
                assert data["usage"]["total_tokens"] > 0
                print("✅ Test Passed")
            else:
                print("⚠️ Warning: Usage data missing")
        else:
            print(f"❌ Test Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Manual Chat Tests...")
    
    # 1. Gemini Basic
    test_chat_completions(provider="gemini", model="models/gemini-2.0-flash")
    time.sleep(3)
    
    # 2. LiteLLM Basic
    test_chat_completions(provider="litellm", model="litellm_proxy/openai/gpt-4o-mini")
    time.sleep(3)
    
    # 3. Test with System Prompt
    test_chat_completions(
        provider="gemini", 
        model="models/gemini-2.0-flash", 
        system_prompt="You are a pirate. Answer everything with 'Arrr!'.",
        user_prompt="How is the weather?"
    )
    
    print("\n🏁 Tests Completed.")

