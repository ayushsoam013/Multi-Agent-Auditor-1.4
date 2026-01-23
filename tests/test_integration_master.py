import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.multi_agent_orchestrator import orchestrator
from app.schemas.agent_schemas import (
    AgentRequest,
    PhotoAgentResponse,
    TextualAgentResponse,
    RCAAgentResponse,
    RCAAnalysisResult,
    RCAIssue,
)


@pytest.mark.asyncio
async def test_orchestrator_master_agent_props():
    # Setup mocks for dependent agents

    # Photo Agent success
    mock_photo_res = MagicMock(spec=PhotoAgentResponse)
    mock_photo_res.status = "success"
    mock_photo_res.processing_time = 1.0
    mock_photo_res.cost = 0.01
    mock_photo_res.analysis = MagicMock()
    mock_photo_res.analysis.task_4 = {}
    orchestrator.photo_agent.process = AsyncMock(return_value=mock_photo_res)

    # Textual Agent success
    mock_textual_res = MagicMock(spec=TextualAgentResponse)
    mock_textual_res.status = "success"
    mock_textual_res.processing_time = 1.0
    mock_textual_res.cost = 0.01
    mock_textual_res.analysis = MagicMock()
    # Mocking attributes accessed by _has_outliers
    mock_textual_res.analysis.task_1 = None
    mock_textual_res.analysis.task_2 = None
    mock_textual_res.analysis.task_4 = MagicMock(product_search_query="query")
    mock_textual_res.analysis.task_5 = None
    mock_textual_res.analysis.task_6 = None
    mock_textual_res.analysis.task_7 = None
    orchestrator.textual_agent.process = AsyncMock(return_value=mock_textual_res)

    # RCA Agent success
    mock_rca_res = MagicMock(spec=RCAAgentResponse)
    mock_rca_res.status = "success"
    mock_rca_res.processing_time = 1.0
    mock_rca_res.cost = 0.01
    mock_rca_res.analysis = RCAAnalysisResult(
        root_cause_summary="None",
        identified_issues=[],
        recommended_verdict="PASS",
        confidence=1.0,
    )
    orchestrator.rca_agent.process = AsyncMock(return_value=mock_rca_res)

    # Use real MasterAgent instance from orchestrator

    request = AgentRequest(
        product_title="Test Product", product_specs="Specs", mcat_name="Category"
    )

    result = await orchestrator.run_audit(request)

    print(f"Master Agent: {result.master_agent}")
    print(f"Master Cost: {result.master_agent.cost}")
    print(f"Master Time: {result.master_agent.processing_time}")
    print(f"Master Decision Code: {result.master_agent.decision_code}")

    # Check expectations
    assert (
        result.master_agent.cost > 0.0
    )  # Expect cost > 0 for PASS now (LLM recommendation)
    assert result.master_agent.processing_time > 0  # Expect some time
    assert result.master_agent.decision_code == "00000"


@pytest.mark.asyncio
async def test_orchestrator_master_agent_fail_cost():
    # Setup mocks for dependent agents to trigger a FAIL

    # Photo Agent with Outlier
    mock_photo_res = MagicMock(spec=PhotoAgentResponse)
    mock_photo_res.status = "success"
    mock_photo_res.processing_time = 1.0
    mock_photo_res.cost = 0.01
    mock_photo_res.analysis = MagicMock()
    mock_photo_res.analysis.task_4 = {}
    orchestrator.photo_agent.process = AsyncMock(return_value=mock_photo_res)

    # Textual Agent success
    mock_textual_res = MagicMock(spec=TextualAgentResponse)
    mock_textual_res.status = "success"
    mock_textual_res.processing_time = 1.0
    mock_textual_res.cost = 0.01
    mock_textual_res.analysis = MagicMock()
    # Mocking attributes accessed by _has_outliers
    mock_textual_res.analysis.task_1 = None
    mock_textual_res.analysis.task_2 = None
    mock_textual_res.analysis.task_4 = MagicMock(product_search_query="query")
    mock_textual_res.analysis.task_5 = None
    mock_textual_res.analysis.task_6 = None
    mock_textual_res.analysis.task_7 = None
    orchestrator.textual_agent.process = AsyncMock(return_value=mock_textual_res)

    # RCA Agent with ISSUES
    mock_rca_res = MagicMock(spec=RCAAgentResponse)
    mock_rca_res.status = "success"
    mock_rca_res.processing_time = 1.0
    mock_rca_res.cost = 0.01
    mock_rca_res.analysis = RCAAnalysisResult(
        root_cause_summary="Mismatch found",
        identified_issues=[
            # Issue that maps to a flag
            RCAIssue(
                issue_type="PHOTO_CATEGORY_MISMATCH",
                description="Bad",
                severity="HIGH",
                evidence="None",
            )
        ],
        recommended_verdict="FAIL",
        confidence=1.0,
    )
    # We need to make sure identified_issues elements have attributes
    # RCAAnalysisResult validation might convert MagicMock to dict if we are not careful
    # But we are using MagicMock(spec=RCAAgentResponse) so analysis is accessed directly.
    # But MasterAgent expects RCAAgentResponse object.

    orchestrator.rca_agent.process = AsyncMock(return_value=mock_rca_res)

    # Mock MasterAgent's LLM service to return cost
    with patch("app.services.llm_manager.llm_manager.get_service") as mock_get_service:
        mock_gen = MagicMock()
        mock_gen.chat_with_usage = AsyncMock(
            return_value={"content": "Fix it", "costing": 0.123}
        )
        mock_get_service.return_value = mock_gen

        # We need to re-init MasterAgent or patch its gen_service directly
        # orchestrator.master_agent.gen_service = mock_gen
        # But BaseAgent sets self.gen_service in __init__.
        # So we should patch it on the instance.
        orchestrator.master_agent.gen_service = mock_gen

        request = AgentRequest(
            product_title="Test Product", product_specs="Specs", mcat_name="Category"
        )

        result = await orchestrator.run_audit(request)

        print(f"Master Agent Fail: {result.master_agent}")
        print(f"Master Cost Fail: {result.master_agent.cost}")
        print(f"Master Decision Code Fail: {result.master_agent.decision_code}")

        assert result.master_agent.cost == 0.123
        assert result.master_agent.decision_code != "00000"
