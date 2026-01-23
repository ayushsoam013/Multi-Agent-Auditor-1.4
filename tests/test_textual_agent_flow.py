import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
from app.schemas.agent_schemas import (
    AgentRequest,
    PhotoAgentResponse,
    TextualAgentResponse,
    TextualAnalysisResult,
    TextualTask1,
    TextualTask2,
    TextualTask3,
    TextualTask4,
    TextualTask5,
    TextualTask6,
    TextualTask7,
    CategoryAgentResponse,
    CategoryAnalysisResult,
    RCAAgentResponse,
    RCAAnalysisResult,
    MasterAgentResponse,
    TaskStatus,
)


@pytest.mark.asyncio
async def test_orchestrator_runs_textual_agent():
    """
    Verify that the orchestrator runs the TextualAgent and passes PhotoAgent results to it.
    """
    # Setup Mocks
    mock_photo_response = PhotoAgentResponse(
        agent_name="PhotoAgent",
        status="success",
        analysis={
            "task_1": {
                "primary_object": "Test Object",
            },
            "task_2": {"ocr_text": ["Sample Text"]},
            "task_3": {"photo_specifications": {"Color": "Red"}},
            "task_4": {
                "severely_cut_off": {"status": "not_outlier", "reason": "visible"},
                "unidentifiable_blur": {"status": "not_outlier", "reason": "clear"},
                "severely_obscured": {"status": "not_outlier", "reason": "clear"},
                "generally_unclear": {"status": "not_outlier", "reason": "clear"},
                "human_blocking_the_product": {
                    "status": "not_outlier",
                    "reason": "no human",
                },
            },
        },
    )

    mock_textual_response = TextualAgentResponse(
        agent_name="TextualAgent",
        status="success",
        analysis=TextualAnalysisResult(
            task_1=TextualTask1(
                spell_error=TaskStatus(status="not_outlier", reason=""),
                duplicate_words=TaskStatus(status="not_outlier", reason=""),
                internal_contradiction=TaskStatus(status="not_outlier", reason=""),
            ),
            task_2=TextualTask2(
                spell_error=TaskStatus(status="not_outlier", reason=""),
                duplicate_specifications=TaskStatus(status="not_outlier", reason=""),
                internal_contradiction=TaskStatus(status="not_outlier", reason=""),
            ),
            task_3=TextualTask3(identified_entities=[]),
            task_4=TextualTask4(product_search_query="query"),
            task_5=TextualTask5(
                photo_title=TaskStatus(status="not_outlier", reason=""),
                photo_specs=TaskStatus(status="not_outlier", reason=""),
                title_specs=TaskStatus(status="not_outlier", reason=""),
                query_internal=TaskStatus(status="not_outlier", reason=""),
                photo_specs_specs=TaskStatus(status="not_outlier", reason=""),
            ),
            task_6=TextualTask6(
                primary_object_category=TaskStatus(status="not_outlier", reason=""),
                query_category=TaskStatus(status="not_outlier", reason=""),
                title_category=TaskStatus(status="not_outlier", reason=""),
            ),
            task_7=TextualTask7(
                mechanism_mismatch=TaskStatus(status="not_outlier", reason=""),
                entity_mismatch=TaskStatus(status="not_outlier", reason=""),
                visual_mimicry=TaskStatus(status="not_outlier", reason=""),
            ),
        ),
    )

    mock_category_response = CategoryAgentResponse(
        agent_name="CategoryAgent",
        status="success",
        analysis=CategoryAnalysisResult(
            suggested_category="Test Category",
            confidence_score=0.9,
            reasoning="Valid category",
            alternative_categories=[],
        ),
    )

    mock_rca_response = RCAAgentResponse(
        agent_name="RCAAgent",
        status="success",
        analysis=RCAAnalysisResult(
            root_cause_summary="No issues",
            identified_issues=[],
            recommended_verdict="PASS",
            confidence=1.0,
        ),
    )

    mock_master_response = MasterAgentResponse(
        agent_name="MasterAgent",
        status="success",
        audit_decision="PASS",
        decision_code="00000",
        confidence_score=1.0,
        reasons=[],
    )

    with (
        patch("app.services.multi_agent_orchestrator.PhotoAgent") as MockPhotoAgent,
        patch("app.services.multi_agent_orchestrator.TextualAgent") as MockTextualAgent,
        # patch(
        #     "app.services.multi_agent_orchestrator.CategoryAgent"
        # ) as MockCategoryAgent,
        patch("app.services.multi_agent_orchestrator.RCAAgent") as MockRCAAgent,
        patch("app.services.multi_agent_orchestrator.MasterAgent") as MockMasterAgent,
    ):
        # Configure instances
        photo_instance = MockPhotoAgent.return_value
        photo_instance.process = AsyncMock(return_value=mock_photo_response)

        textual_instance = MockTextualAgent.return_value
        textual_instance.process = AsyncMock(return_value=mock_textual_response)

        # category_instance = MockCategoryAgent.return_value
        # category_instance.process = AsyncMock(return_value=mock_category_response)

        rca_instance = MockRCAAgent.return_value
        rca_instance.process = AsyncMock(return_value=mock_rca_response)

        master_instance = MockMasterAgent.return_value
        master_instance.process = AsyncMock(return_value=mock_master_response)

        # Initialize Orchestrator
        orchestrator = MultiAgentOrchestrator()

        # Create Request
        request = AgentRequest(
            product_title="Test Title",
            product_specs="Test Specs",
            mcat_name="Test Category",
            image_path="dummy.jpg",
        )

        # Run Audit
        result = await orchestrator.run_audit(request)

        # Assertions

        # 1. Verify Photo Agent was called
        photo_instance.process.assert_called_once()

        # 2. Verify Textual Agent was called
        textual_instance.process.assert_called_once()

        # 3. Verify Textual Agent received the correct context (Photo results)
        call_args = textual_instance.process.call_args
        passed_request = call_args[0][0]
        assert "photo_agent" in passed_request.context
        assert passed_request.context["photo_agent"] == mock_photo_response
        assert passed_request.mcat_name == "Test Category"

        # 4. Verify Result structure
        assert result.textual_agent == mock_textual_response
