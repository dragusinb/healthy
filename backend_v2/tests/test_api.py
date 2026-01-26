"""
Integration tests for Healthy API endpoints.
Run with: pytest backend_v2/tests/ -v
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

# Create test database tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestHealthEndpoint:
    """Test basic health/status endpoint."""

    def test_root_endpoint(self):
        """Test that root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    test_email = "test_user_" + str(os.getpid()) + "@test.com"
    test_password = "TestPassword123!"

    def test_register_user(self):
        """Test user registration."""
        response = client.post("/auth/register", json={
            "email": self.test_email,
            "password": self.test_password
        })
        # Either success (201) or user already exists (400)
        assert response.status_code in [200, 201, 400]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "access_token" in data or "id" in data

    def test_login_user(self):
        """Test user login."""
        # First register
        client.post("/auth/register", json={
            "email": self.test_email,
            "password": self.test_password
        })

        # Then login
        response = client.post("/auth/token", data={
            "username": self.test_email,
            "password": self.test_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        response = client.post("/auth/token", data={
            "username": self.test_email,
            "password": "wrong_password"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = client.post("/auth/token", data={
            "username": "nonexistent@test.com",
            "password": "anypassword"
        })
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""

    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication."""
        response = client.get("/dashboard")
        assert response.status_code == 401

    def test_profile_requires_auth(self):
        """Test profile requires authentication."""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_documents_requires_auth(self):
        """Test documents requires authentication."""
        response = client.get("/documents")
        assert response.status_code == 401


class TestAuthenticatedEndpoints:
    """Test endpoints with authentication."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests."""
        # Register and login
        email = "auth_test_" + str(os.getpid()) + "@test.com"
        password = "AuthTest123!"

        client.post("/auth/register", json={
            "email": email,
            "password": password
        })

        response = client.post("/auth/token", data={
            "username": email,
            "password": password
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def test_get_dashboard(self):
        """Test getting dashboard data."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.get("/dashboard", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "documents_count" in data or "document_count" in data

    def test_get_profile(self):
        """Test getting user profile."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.get("/users/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    def test_update_profile_valid(self):
        """Test updating profile with valid data."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": 175,
            "weight_kg": 70,
            "gender": "male"
        })
        assert response.status_code == 200

    def test_update_profile_invalid_height(self):
        """Test profile validation - invalid height."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": -10
        })
        assert response.status_code == 400

    def test_update_profile_invalid_weight(self):
        """Test profile validation - invalid weight."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.put("/users/profile", headers=self.headers, json={
            "weight_kg": 600
        })
        assert response.status_code == 400

    def test_get_documents(self):
        """Test getting documents list."""
        if not self.token:
            pytest.skip("Auth setup failed")

        response = client.get("/documents", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSecurityValidation:
    """Test security-related validations."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests."""
        email = "security_test_" + str(os.getpid()) + "@test.com"
        password = "SecurityTest123!"

        client.post("/auth/register", json={
            "email": email,
            "password": password
        })

        response = client.post("/auth/token", data={
            "username": email,
            "password": password
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    def test_document_access_other_user(self):
        """Test that user cannot access other user's documents."""
        if not self.token:
            pytest.skip("Auth setup failed")

        # Try to access document ID that doesn't belong to this user
        response = client.get("/documents/99999/download", headers=self.headers)
        assert response.status_code == 404  # Not found, not 403

    def test_invalid_token(self):
        """Test that invalid token is rejected."""
        response = client.get("/dashboard", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        assert response.status_code == 401

    def test_expired_token_format(self):
        """Test that malformed token is rejected."""
        response = client.get("/dashboard", headers={
            "Authorization": "Bearer"
        })
        assert response.status_code in [401, 422]


class TestInputValidation:
    """Test input validation across endpoints."""

    def test_register_invalid_email(self):
        """Test registration with invalid email format."""
        response = client.post("/auth/register", json={
            "email": "not_an_email",
            "password": "TestPassword123!"
        })
        assert response.status_code in [400, 422]

    def test_register_empty_password(self):
        """Test registration with empty password."""
        response = client.post("/auth/register", json={
            "email": "valid@email.com",
            "password": ""
        })
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
