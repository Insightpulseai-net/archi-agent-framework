# apps/pulser-hub/tests/test_api.py
"""Tests for Pulser-Hub API endpoints."""

import pytest
from fastapi.testclient import TestClient

# Import will be available when running from apps/pulser-hub directory
try:
    from api.main import app
except ImportError:
    # Fallback for running from repo root
    import sys
    sys.path.insert(0, "apps/pulser-hub")
    from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pulser-hub"
        assert "version" in data

    def test_health_check_integrations(self, client):
        """Test health check includes integrations status."""
        response = client.get("/health")
        data = response.json()
        assert "integrations" in data
        assert "github" in data["integrations"]
        assert "databricks" in data["integrations"]
        assert "supabase" in data["integrations"]


class TestComplianceEndpoints:
    """Tests for compliance endpoints."""

    def test_compliance_summary(self, client):
        """Test compliance summary returns all forms."""
        response = client.get("/compliance/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_forms"] == 36
        assert "compliant" in data
        assert "categories" in data

    def test_compliance_form_1700(self, client):
        """Test Form 1700 compliance status."""
        response = client.get("/compliance/status/1700")
        assert response.status_code == 200
        data = response.json()
        assert data["form_number"] == "1700"
        assert data["form_name"] == "Annual Income Tax Return"
        assert "compliance_percentage" in data

    def test_compliance_unknown_form(self, client):
        """Test unknown form returns 404."""
        response = client.get("/compliance/status/9999")
        assert response.status_code == 404


class TestPipelineEndpoints:
    """Tests for pipeline endpoints."""

    def test_run_pipeline_full(self, client):
        """Test running full pipeline."""
        response = client.post(
            "/pipeline/run",
            json={"action": "run_full_pipeline"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["action"] == "run_full_pipeline"
        assert data["status"] in ["RUNNING", "PENDING"]

    def test_run_pipeline_ingestion(self, client):
        """Test running ingestion only."""
        response = client.post(
            "/pipeline/run",
            json={"action": "run_ingestion"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "run_ingestion"

    def test_run_pipeline_invalid_action(self, client):
        """Test invalid action returns 422."""
        response = client.post(
            "/pipeline/run",
            json={"action": "invalid_action"}
        )
        assert response.status_code == 422

    def test_pipeline_status_not_found(self, client):
        """Test unknown run ID returns appropriate response."""
        response = client.get("/pipeline/status/unknown-run-id")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_FOUND"


class TestGitHubEndpoints:
    """Tests for GitHub endpoints."""

    def test_github_status(self, client):
        """Test GitHub status endpoint."""
        response = client.get("/github/status")
        assert response.status_code == 200
        data = response.json()
        assert data["app_id"] == "2191216"
        assert data["client_id"] == "Iv23liwGL7fnYySPPAjS"

    def test_github_commit_validation(self, client):
        """Test commit endpoint validates input."""
        response = client.post(
            "/github/commit",
            json={
                "commit_message": "Test commit",
                # Missing required 'files' field
            }
        )
        assert response.status_code == 422


class TestOdooEndpoints:
    """Tests for Odoo deployment endpoints."""

    def test_deploy_module(self, client):
        """Test module deployment endpoint."""
        response = client.post(
            "/odoo/deploy",
            json={
                "module_name": "ipai_bir_compliance",
                "environment": "staging",
                "run_tests": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "deployment_id" in data
        assert data["module_name"] == "ipai_bir_compliance"
        assert data["environment"] == "staging"

    def test_deploy_status_not_found(self, client):
        """Test unknown deployment ID."""
        response = client.get("/odoo/status/unknown-deploy-id")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NOT_FOUND"


class TestChatGPTEndpoint:
    """Tests for ChatGPT Actions endpoint."""

    def test_function_call_run_pipeline(self, client):
        """Test ChatGPT function call for pipeline."""
        response = client.post(
            "/chatgpt/function-call",
            json={
                "function": "run_pipeline",
                "arguments": {"action": "run_compliance"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "next_steps" in data

    def test_function_call_query_compliance(self, client):
        """Test ChatGPT function call for compliance."""
        response = client.post(
            "/chatgpt/function-call",
            json={
                "function": "query_compliance",
                "arguments": {"form_number": "1700"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_function_call_invalid_function(self, client):
        """Test invalid function returns error."""
        response = client.post(
            "/chatgpt/function-call",
            json={
                "function": "invalid_function",
                "arguments": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestWebhookEndpoint:
    """Tests for GitHub webhook endpoint."""

    def test_webhook_missing_signature(self, client):
        """Test webhook without signature."""
        response = client.post(
            "/webhook/github",
            json={"action": "opened"},
            headers={"X-GitHub-Event": "pull_request"}
        )
        # Should still process (signature validation skipped without secret)
        assert response.status_code in [200, 400]

    def test_webhook_push_event(self, client):
        """Test push event webhook."""
        response = client.post(
            "/webhook/github",
            json={
                "ref": "refs/heads/main",
                "commits": [{"id": "abc123", "modified": ["docs/test.md"]}],
                "repository": {"full_name": "test/repo"},
                "sender": {"login": "testuser"},
                "pusher": {"name": "testuser"},
            },
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "test-delivery-123",
            }
        )
        assert response.status_code == 200
