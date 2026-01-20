"""
Test cases to validate litellm_proxy/ prefix normalization
"""

from app.services.litellm_service import LiteLLMService

def test_prefix_normalization_with_provider_path():
    """Test that provider/model format gets litellm_proxy/ prefix added"""
    service = LiteLLMService()
    
    # Test with google model
    result = service._ensure_litellm_proxy_prefix("google/gemini-2.5-flash")
    assert result == "litellm_proxy/google/gemini-2.5-flash", f"Expected litellm_proxy/google/gemini-2.5-flash, got {result}"
    
    # Test with openai model
    result = service._ensure_litellm_proxy_prefix("openai/gpt-4o-mini")
    assert result == "litellm_proxy/openai/gpt-4o-mini", f"Expected litellm_proxy/openai/gpt-4o-mini, got {result}"

def test_prefix_normalization_already_has_prefix():
    """Test that models with litellm_proxy/ prefix are not double-prefixed"""
    service = LiteLLMService()
    
    # Test with google model (already has prefix)
    result = service._ensure_litellm_proxy_prefix("litellm_proxy/google/gemini-2.5-flash")
    assert result == "litellm_proxy/google/gemini-2.5-flash", f"Expected litellm_proxy/google/gemini-2.5-flash, got {result}"
    
    # Test with openai model (already has prefix)
    result = service._ensure_litellm_proxy_prefix("litellm_proxy/openai/gpt-4o-mini")
    assert result == "litellm_proxy/openai/gpt-4o-mini", f"Expected litellm_proxy/openai/gpt-4o-mini, got {result}"

def test_default_model_names():
    """Test that default models are set correctly from config"""
    service = LiteLLMService()
    
    # Should be without litellm_proxy/ prefix (added at runtime)
    # Default is google/gemini-2.5-flash
    assert service.model_name == "google/gemini-2.5-flash", f"Expected google/gemini-2.5-flash, got {service.model_name}"
    
    # When used, it should get the prefix
    prefixed = service._ensure_litellm_proxy_prefix(service.model_name)
    assert prefixed == "litellm_proxy/google/gemini-2.5-flash", f"Expected litellm_proxy/google/gemini-2.5-flash, got {prefixed}"


if __name__ == "__main__":
    print("Running prefix normalization tests...")
    
    print("\n1. Testing provider/model format...")
    test_prefix_normalization_with_provider_path()
    print("   ✓ Passed")
    
    print("\n2. Testing models with existing prefix...")
    test_prefix_normalization_already_has_prefix()
    print("   ✓ Passed")
    
    print("\n3. Testing default model configuration...")
    test_default_model_names()
    print("   ✓ Passed")
    
    print("\n✅ All tests passed!")
