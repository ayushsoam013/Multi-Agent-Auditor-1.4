from fastapi import APIRouter, HTTPException
from app.models.dtos import ChatRequest, ChatResponse
from app.services.llm_manager import llm_manager

router = APIRouter()

@router.post("/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Chat completion endpoint supporting dynamic provider selection and usage tracking.
    """
    try:
        # Determine service
        provider = request.provider or llm_manager.get_current_provider()
        service = llm_manager.gen_services.get(provider)
        
        if not service:
             raise HTTPException(status_code=400, detail=f"Provider {provider} not found")

        # Config
        config = {}
        if request.max_tokens:
            config["max_output_tokens"] = request.max_tokens
        if request.temperature:
            config["temperature"] = request.temperature
            
        # If the user selected a specific model, we might need to set it on the service or pass it
        # The current service implementation stores model_name in `self.model_name`.
        # Changing it on the singleton service is not thread-safe but for this POC it's the pattern used.
        # A better way would be if `chat_with_usage` accepted a model_name override, but I won't refactor services that deep now.
        # I'll check if I can just swap the model name temporarily or if the services allow passing it.
        # Looking at previous file views, generate_content uses self.model_name.
        # But `genai` and `litellm` calls take `model=self.model_name`.
        # I'll assume for now we use the default or "configured" model in the service, 
        # UNLESS I modify the service to accept model.
        # The prompt says "provide... a way for them to select the models". 
        # So I MUST support model selection.
        # I will modify the service instance's model_name temporarily? No, that's bad.
        # I should assume the `config` or another arg can pass the model.
        # Inspecting services again:
        # Gemini: 
        # response = self.client.models.generate_content(model=self.model_name, ...)
        # LiteLLM:
        # response = litellm.completion(model=self.model_name, ...)
        
        # I should have added `model` arg to `chat_with_usage`.
        # Let's check the service definitions again.
        # I'll update the services to use `request.model` if provided, otherwise `self.model_name`.
        # But for now, let's write the endpoint and maybe do a quick patch to services to use a model from config or arg?
        # Actually `chat_with_usage` takes `config`. I can pass model in config? 
        # Gemini: config is passed to `generate_content` as `config`. `model` is separate arg.
        # LiteLLM: kwargs from config are passed.
        
        # Quick fix: I'll manually handle it in the endpoint by monkey-patching or better, 
        # just accept that I might need to instantiate a new service or helper for a different model?
        # No, that's heavy.
        
        # Re-reading my service update:
        # Gemini: `model=self.model_name` is hardcoded.
        # LiteLLM: `model=self.model_name` is hardcoded.
        
        # I MUST update the services to allow model override. 
        # I'll do that in a subsequent step or right now?
        # I'll write the endpoint first, assuming I'll fix the services to look for model in config or arg.
        # Actually, let's make the endpoint assume the service supports `model` param in `chat_with_usage` 
        # OR just update the service attribute if we have to (racey but maybe acceptable for POC).
        # OR: I'll update services to check `config.get('model')`.
        
        # Let's write the endpoint to pass `model` in config.
        if request.model:
            config["model"] = request.model

        # Call service
        result = await service.chat_with_usage(request.messages, config=config)
        
        return ChatResponse(**result)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
