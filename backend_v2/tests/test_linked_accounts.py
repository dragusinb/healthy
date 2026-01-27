"""
Comprehensive linked accounts (provider) flow tests.
Tests adding, updating, and managing provider accounts.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_linked.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestLinkedAccountManagement:
    """Test linked account CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"linked_test_{int(time.time())}@test.com"
        self.password = "LinkedTestPassword123"
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

    def test_get_linked_accounts_empty(self):
        """Test getting linked accounts for new user."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/users/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "linked_accounts" in data
        assert isinstance(data["linked_accounts"], list)

    def test_link_account_regina_maria(self):
        """Test linking a Regina Maria account."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.post("/users/link-account", headers=self.headers, json={
            "provider_name": "Regina Maria",
            "username": "test_user",
            "password": "test_password"
        })
        # Should succeed (creates account, but sync will fail since credentials are fake)
        assert response.status_code in [200, 201]

    def test_link_account_synevo(self):
        """Test linking a Synevo account."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.post("/users/link-account", headers=self.headers, json={
            "provider_name": "Synevo",
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code in [200, 201]

    def test_link_account_invalid_provider(self):
        """Test linking with invalid provider name."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.post("/users/link-account", headers=self.headers, json={
            "provider_name": "InvalidProvider",
            "username": "test_user",
            "password": "test_password"
        })
        # Should fail with 400 or similar
        assert response.status_code in [400, 422]

    def test_link_account_missing_username(self):
        """Test linking without username."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.post("/users/link-account", headers=self.headers, json={
            "provider_name": "Regina Maria",
            "password": "test_password"
        })
        assert response.status_code == 422

    def test_link_account_missing_password(self):
        """Test linking without password."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.post("/users/link-account", headers=self.headers, json={
            "provider_name": "Regina Maria",
            "username": "test_user"
        })
        assert response.status_code == 422

    def test_link_account_requires_auth(self):
        """Test that linking account requires authentication."""
        response = client.post("/users/link-account", json={
            "provider_name": "Regina Maria",
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code == 401


class TestSyncStatus:
    """Test sync status endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user with linked account."""
        self.email = f"sync_test_{int(time.time())}@test.com"
        self.password = "SyncTestPassword123"
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

    def test_get_sync_status_no_account(self):
        """Test getting sync status without linked account."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/users/sync-status/Regina Maria", headers=self.headers)
        # Should return idle status or 404
        assert response.status_code in [200, 404]

    def test_sync_status_requires_auth(self):
        """Test sync status requires authentication."""
        response = client.get("/users/sync-status/Regina Maria")
        assert response.status_code == 401


class TestAccountDeletion:
    """Test linked account deletion."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"delete_acc_test_{int(time.time())}@test.com"
        self.password = "DeleteAccTestPassword123"
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

    def test_delete_nonexistent_account(self):
        """Test deleting non-existent linked account."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.delete("/users/accounts/99999", headers=self.headers)
        assert response.status_code == 404

    def test_delete_account_requires_auth(self):
        """Test deleting linked account requires authentication."""
        response = client.delete("/users/accounts/1")
        assert response.status_code == 401


class TestAccountIsolation:
    """Test that users can only access their own linked accounts."""

    def test_users_cannot_access_others_accounts(self):
        """Test that users cannot access other users' linked accounts."""
        # Create user 1
        email1 = f"user1_acc_{int(time.time())}@test.com"
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
        email2 = f"user2_acc_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email2,
            "password": "Password123"
        })
        token2 = client.post("/auth/token", data={
            "username": email2,
            "password": "Password123"
        }).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 creates an account
        client.post("/users/link-account", headers=headers1, json={
            "provider_name": "Regina Maria",
            "username": "user1_rm",
            "password": "password1"
        })

        # User 2 tries to delete user 1's account (ID 1)
        response = client.delete("/users/accounts/1", headers=headers2)
        # Should fail with 404 (not found for this user) or 403
        assert response.status_code in [404, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
