import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.schemas.agent_schemas import MultiAgentAuditResult, MasterAgentResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    with patch("app.api.v1.endpoints.audit.orchestrator") as mock:
        # Setup the mock to return a dummy result
        mock.run_audit = AsyncMock()

        # Create a minimal valid response object
        dummy_result = MultiAgentAuditResult(
            audit_id="test_id_123",
            master_agent=MasterAgentResponse(
                agent_name="MasterAgent",
                audit_decision="PASS",
                decision_code="00000",
                confidence_score=0.95,
                reasons=["Test reason"],
            ),
        )
        mock.run_audit.return_value = dummy_result
        yield mock


def test_multi_agent_audit_with_mcat_name(client, mock_orchestrator):
    """
    Test that the /multi-agent endpoint correctly accepts 'mcat_name'
    and passes it to the orchestrator.
    """
    # dummy image content
    file_content = b"fake image content"
    files = {"file": ("test_image.jpg", file_content, "image/jpeg")}

    # Form data including mcat_name
    data = {
        "product_title": "Test Product Title",
        "product_specs": "Test Specs",
        "mcat_name": "Test Category",
    }

    response = client.post("/api/v1/audit/multi-agent", data=data, files=files)

    # Assert 200 OK
    assert response.status_code == 200

    # Verify orchestrator was called
    assert mock_orchestrator.run_audit.called

    # Get the arguments passed to run_audit
    call_args = mock_orchestrator.run_audit.call_args
    agent_request = call_args[0][0]  # First positional argument

    # Verify fields in the request object
    assert agent_request.product_title == "Test Product Title"
    assert agent_request.product_specs == "Test Specs"
    assert agent_request.mcat_name == "Test Category"


def test_multi_agent_audit_without_mcat_name(client, mock_orchestrator):
    """
    Test that 'mcat_name' is optional and handled correctly when missing.
    """
    files = {"file": ("test_image.jpg", b"content", "image/jpeg")}
    data = {
        "product_title": "Test Product Title",
        "product_specs": "Test Specs",
        # mcat_name omitted
    }

    response = client.post("/api/v1/audit/multi-agent", data=data, files=files)

    assert response.status_code == 200

    agent_request = mock_orchestrator.run_audit.call_args[0][0]
    assert agent_request.mcat_name is None
