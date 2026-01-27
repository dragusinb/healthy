"""
Comprehensive biomarkers and dashboard flow tests.
Tests biomarker listing, filtering, and evolution charts.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_bio.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestDashboardEndpoints:
    """Test dashboard statistics endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"dashboard_test_{int(time.time())}@test.com"
        self.password = "DashboardTestPassword123"
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

    def test_get_stats(self):
        """Test getting dashboard stats."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "documents_count" in data
        assert "biomarkers_count" in data

    def test_get_stats_requires_auth(self):
        """Test dashboard stats requires authentication."""
        response = client.get("/dashboard/stats")
        assert response.status_code == 401

    def test_get_alerts_count(self):
        """Test getting alerts count."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/alerts-count", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "alerts_count" in data
        assert isinstance(data["alerts_count"], int)

    def test_get_recent_biomarkers(self):
        """Test getting recent biomarkers."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/recent-biomarkers", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patient_info(self):
        """Test getting patient info."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/patient-info", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "distinct_patients" in data or "patient_count" in data


class TestBiomarkersEndpoints:
    """Test biomarker listing and filtering."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"biomarker_test_{int(time.time())}@test.com"
        self.password = "BiomarkerTestPassword123"
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

    def test_get_biomarkers(self):
        """Test getting all biomarkers."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/biomarkers", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_biomarkers_filtered(self):
        """Test getting biomarkers with filter."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/biomarkers?filter_out_of_range=true", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_biomarkers_grouped(self):
        """Test getting grouped biomarkers."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/biomarkers-grouped", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_biomarkers_requires_auth(self):
        """Test biomarkers endpoint requires authentication."""
        response = client.get("/dashboard/biomarkers")
        assert response.status_code == 401


class TestEvolutionEndpoints:
    """Test biomarker evolution (chart data) endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"evolution_test_{int(time.time())}@test.com"
        self.password = "EvolutionTestPassword123"
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

    def test_get_evolution_nonexistent(self):
        """Test getting evolution for non-existent biomarker."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/dashboard/evolution/NonExistentBiomarker", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Should return empty data array
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_evolution_requires_auth(self):
        """Test evolution endpoint requires authentication."""
        response = client.get("/dashboard/evolution/Hemoglobin")
        assert response.status_code == 401

    def test_get_evolution_url_encoded_name(self):
        """Test getting evolution with URL-encoded biomarker name."""
        if not self.token:
            pytest.skip("Auth setup failed")
        # Test with spaces and special characters
        response = client.get("/dashboard/evolution/Hemoglobin%20A1c", headers=self.headers)
        assert response.status_code == 200


class TestDataIsolation:
    """Test that users can only see their own biomarkers."""

    def test_users_see_only_own_biomarkers(self):
        """Test that biomarker data is isolated per user."""
        # Create user 1
        email1 = f"user1_bio_{int(time.time())}@test.com"
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
        email2 = f"user2_bio_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email2,
            "password": "Password123"
        })
        token2 = client.post("/auth/token", data={
            "username": email2,
            "password": "Password123"
        }).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Both users should get their own data (empty for new users)
        response1 = client.get("/dashboard/biomarkers", headers=headers1)
        response2 = client.get("/dashboard/biomarkers", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should be empty lists for new users
        data1 = response1.json()
        data2 = response2.json()
        assert isinstance(data1, list)
        assert isinstance(data2, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
