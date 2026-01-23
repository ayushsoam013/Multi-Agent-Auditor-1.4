import json
import logging
import mimetypes
from typing import Dict, Any, Optional
from google.genai import types
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import (
    AgentRequest,
    PhotoAgentResponse,
    PhotoAnalysisResult,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class PhotoAgent(BaseAgent):
    """
    Multi-modal agent specialized in visual product analysis.
    Uses Vision models to extract data and assess image quality.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="PhotoAgent",
            model_name=model_name or settings.GEMINI_GEN_MODEL,
            response_class=PhotoAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Photo Logic:
        1. Object Detection & Description: What is the product?
        2. OCR: What text is physically on the product or packaging?
        3. Visual Specs: Extract technical details seen only in the image.
        4. Visibility Assessment: Is the photo too blurry, cut off, or obscured for a listing?
        """
        if not request.image_path and not request.image_url:
            raise ValueError("PhotoAgent requires an image_path or image_url")

        # Prepare prompt
        prompt = self._get_photo_prompt()

        # Prepare parts (text + image)
        parts = [types.Part(text=prompt)]

        if request.image_path:
            with open(request.image_path, "rb") as f:
                image_data = f.read()
                mime_type, _ = mimetypes.guess_type(request.image_path)
                if not mime_type:
                    mime_type = "image/jpeg"  # Fallback

                parts.append(
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type=mime_type,
                    )
                )
        # Note: image_url handling would go here if needed,
        # but usually we download it first in the orchestrator or api layer.

        # Call LLM
        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": parts}],
            config={"response_mime_type": "application/json"},
        )

        raw_text = response.get("content", "{}")
        try:
            # Clean up potential markdown formatting if not handled by response_mime_type
            if raw_text.startswith("```json"):
                raw_text = raw_text.strip("```json").strip("```").strip()

            analysis_dict = json.loads(raw_text)
            analysis_dict["_cost"] = response.get("costing", 0.0)
            return analysis_dict
        except Exception as e:
            logger.error(f"Failed to parse PhotoAgent response: {raw_text}")
            raise e

    def _get_photo_prompt(self) -> str:
        return """
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
"""

    def _validate_input(self, request: AgentRequest):
        if not request.image_path and not request.image_url:
            raise ValueError("PhotoAgent requires an image source.")
