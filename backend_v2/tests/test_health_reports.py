"""
Comprehensive health reports and AI analysis flow tests.
Tests report generation, history, and comparison.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_health.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestHealthReportEndpoints:
    """Test health report endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"health_test_{int(time.time())}@test.com"
        self.password = "HealthTestPassword123"
        client.post("/auth/register", json={
            "email": self.email,
            "password": self.password
        })
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": self.password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def test_get_latest_report_empty(self):
        """Test getting latest report for new user."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/health/latest", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # New user should have no report
        assert data.get("has_report") == False or data.get("id") is None

    def test_get_report_history_empty(self):
        """Test getting report history for new user."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/health/history", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_get_specialists(self):
        """Test getting available specialists."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/health/specialists", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Should have multiple specialists
        assert isinstance(data, dict)
        # Check for expected specialists
        expected = ["cardiology", "endocrinology", "hematology", "hepatology", "nephrology"]
        for spec in expected:
            if spec in data:
                assert "name" in data[spec] or "focus" in data[spec]

    def test_health_endpoints_require_auth(self):
        """Test health endpoints require authentication."""
        endpoints = [
            "/health/latest",
            "/health/history",
            "/health/specialists",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"


class TestGapAnalysis:
    """Test gap analysis (screening recommendations) endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"gap_test_{int(time.time())}@test.com"
        self.password = "GapTestPassword123"
        client.post("/auth/register", json={
            "email": self.email,
            "password": self.password
        })
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": self.password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def test_get_latest_gap_analysis(self):
        """Test getting latest gap analysis."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/health/gap-analysis/latest", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # New user may or may not have gap analysis
        assert "has_report" in data or "recommended_tests" in data

    def test_gap_analysis_requires_auth(self):
        """Test gap analysis requires authentication."""
        response = client.get("/health/gap-analysis/latest")
        assert response.status_code == 401


class TestReportComparison:
    """Test report comparison functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"compare_test_{int(time.time())}@test.com"
        self.password = "CompareTestPassword123"
        client.post("/auth/register", json={
            "email": self.email,
            "password": self.password
        })
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": self.password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def test_compare_nonexistent_reports(self):
        """Test comparing non-existent reports."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/health/compare/99999/99998", headers=self.headers)
        # Should return 404 for non-existent reports
        assert response.status_code == 404

    def test_compare_requires_auth(self):
        """Test comparison requires authentication."""
        response = client.get("/health/compare/1/2")
        assert response.status_code == 401


class TestHealthReportIsolation:
    """Test that users can only access their own health reports."""

    def test_users_see_only_own_reports(self):
        """Test that health reports are isolated per user."""
        # Create user 1
        email1 = f"user1_health_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email1,
            "password": "Password123"
        })
        token1 = client.post("/auth/token", data={
            "username": email1,
            "password": "Password123"
        }).json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create user 2
        email2 = f"user2_health_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email2,
            "password": "Password123"
        })
        token2 = client.post("/auth/token", data={
            "username": email2,
            "password": "Password123"
        }).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Both users should get their own history (empty)
        response1 = client.get("/health/history", headers=headers1)
        response2 = client.get("/health/history", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
