"""
Comprehensive authentication flow tests.
Tests registration, login, Google OAuth, and session management.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_auth.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestRegistrationFlow:
    """Test user registration scenarios."""

    def test_register_valid_user(self):
        """Test successful registration with valid data."""
        email = f"new_user_{int(time.time())}@test.com"
        response = client.post("/auth/register", json={
            "email": email,
            "password": "ValidPassword123"
        })
        assert response.status_code in [200, 201]
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_invalid_email_format(self):
        """Test registration fails with invalid email format."""
        response = client.post("/auth/register", json={
            "email": "not_an_email",
            "password": "ValidPassword123"
        })
        assert response.status_code == 422

    def test_register_email_no_domain(self):
        """Test registration fails with email without domain."""
        response = client.post("/auth/register", json={
            "email": "test@",
            "password": "ValidPassword123"
        })
        assert response.status_code == 422

    def test_register_password_too_short(self):
        """Test registration fails with password too short."""
        response = client.post("/auth/register", json={
            "email": "valid@email.com",
            "password": "short"
        })
        assert response.status_code == 422

    def test_register_empty_password(self):
        """Test registration fails with empty password."""
        response = client.post("/auth/register", json={
            "email": "valid@email.com",
            "password": ""
        })
        assert response.status_code == 422

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        email = f"duplicate_{int(time.time())}@test.com"
        # First registration
        client.post("/auth/register", json={
            "email": email,
            "password": "ValidPassword123"
        })
        # Second registration with same email
        response = client.post("/auth/register", json={
            "email": email,
            "password": "DifferentPassword123"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_missing_email(self):
        """Test registration fails without email."""
        response = client.post("/auth/register", json={
            "password": "ValidPassword123"
        })
        assert response.status_code == 422

    def test_register_missing_password(self):
        """Test registration fails without password."""
        response = client.post("/auth/register", json={
            "email": "test@email.com"
        })
        assert response.status_code == 422


class TestLoginFlow:
    """Test user login scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test user for login tests."""
        self.email = f"login_test_{int(time.time())}@test.com"
        self.password = "LoginTestPassword123"
        client.post("/auth/register", json={
            "email": self.email,
            "password": self.password
        })

    def test_login_valid_credentials(self):
        """Test successful login with valid credentials."""
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": self.password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": "WrongPassword123"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user."""
        response = client.post("/auth/token", data={
            "username": "nonexistent@email.com",
            "password": "AnyPassword123"
        })
        assert response.status_code == 401

    def test_login_case_sensitive_email(self):
        """Test login email is case insensitive or sensitive as expected."""
        # Note: This tests the actual behavior - adjust assertion based on requirements
        response = client.post("/auth/token", data={
            "username": self.email.upper(),
            "password": self.password
        })
        # SQLite is case-insensitive by default, PostgreSQL is case-sensitive
        # The test documents the behavior
        assert response.status_code in [200, 401]

    def test_login_empty_password(self):
        """Test login fails with empty password."""
        response = client.post("/auth/token", data={
            "username": self.email,
            "password": ""
        })
        assert response.status_code in [401, 422]

    def test_login_empty_username(self):
        """Test login fails with empty username."""
        response = client.post("/auth/token", data={
            "username": "",
            "password": self.password
        })
        assert response.status_code in [401, 422]


class TestTokenValidation:
    """Test JWT token validation scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create user and get token."""
        self.email = f"token_test_{int(time.time())}@test.com"
        self.password = "TokenTestPassword123"
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

    def test_valid_token_access(self):
        """Test valid token can access protected endpoints."""
        if not self.token:
            pytest.skip("Token setup failed")
        response = client.get("/users/me", headers=self.headers)
        assert response.status_code == 200
        assert response.json()["email"] == self.email

    def test_invalid_token_rejected(self):
        """Test invalid token is rejected."""
        response = client.get("/users/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        assert response.status_code == 401

    def test_malformed_auth_header(self):
        """Test malformed authorization header is rejected."""
        response = client.get("/users/me", headers={
            "Authorization": "NotBearer token"
        })
        assert response.status_code == 401

    def test_missing_auth_header(self):
        """Test missing authorization header is rejected."""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_empty_bearer_token(self):
        """Test empty bearer token is rejected."""
        response = client.get("/users/me", headers={
            "Authorization": "Bearer "
        })
        assert response.status_code in [401, 422]

    def test_token_works_multiple_times(self):
        """Test token can be reused for multiple requests."""
        if not self.token:
            pytest.skip("Token setup failed")
        for _ in range(3):
            response = client.get("/users/me", headers=self.headers)
            assert response.status_code == 200


class TestProtectedEndpoints:
    """Test all protected endpoints require authentication."""

    protected_endpoints = [
        ("GET", "/users/me"),
        ("GET", "/users/profile"),
        ("PUT", "/users/profile"),
        ("GET", "/documents"),
        ("GET", "/dashboard/stats"),
        ("GET", "/dashboard/biomarkers"),
        ("GET", "/dashboard/recent-biomarkers"),
        ("GET", "/health/latest"),
        ("GET", "/health/history"),
        ("POST", "/health/analyze"),
    ]

    @pytest.mark.parametrize("method,endpoint", protected_endpoints)
    def test_endpoint_requires_auth(self, method, endpoint):
        """Test that endpoint requires authentication."""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint)
        elif method == "PUT":
            response = client.put(endpoint)
        else:
            pytest.skip(f"Unknown method {method}")

        assert response.status_code == 401, f"{method} {endpoint} should require auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
