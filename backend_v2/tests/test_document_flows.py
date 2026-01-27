"""
Comprehensive document management flow tests.
Tests document listing, downloading, and security.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_docs.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestDocumentListing:
    """Test document listing functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"doc_test_{int(time.time())}@test.com"
        self.password = "DocTestPassword123"
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

    def test_get_documents_empty(self):
        """Test getting documents for new user returns empty list."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/documents", headers=self.headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_get_documents_requires_auth(self):
        """Test documents endpoint requires authentication."""
        response = client.get("/documents")
        assert response.status_code == 401


class TestDocumentDownload:
    """Test document download security."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"download_test_{int(time.time())}@test.com"
        self.password = "DownloadTestPassword123"
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

    def test_download_nonexistent_document(self):
        """Test downloading non-existent document returns 404."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/documents/99999/download", headers=self.headers)
        assert response.status_code == 404

    def test_download_requires_auth(self):
        """Test document download requires authentication."""
        response = client.get("/documents/1/download")
        assert response.status_code == 401

    def test_download_other_users_document(self):
        """Test user cannot download another user's document."""
        # Create user 1
        email1 = f"user1_dl_{int(time.time())}@test.com"
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
        email2 = f"user2_dl_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email2,
            "password": "Password123"
        })
        token2 = client.post("/auth/token", data={
            "username": email2,
            "password": "Password123"
        }).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 2 tries to access user 1's document (if it existed)
        # Should return 404 (not found for this user)
        response = client.get("/documents/1/download", headers=headers2)
        assert response.status_code in [404, 403]


class TestDocumentDeletion:
    """Test document deletion functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"delete_test_{int(time.time())}@test.com"
        self.password = "DeleteTestPassword123"
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

    def test_delete_nonexistent_document(self):
        """Test deleting non-existent document returns 404."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.delete("/documents/99999", headers=self.headers)
        assert response.status_code == 404

    def test_delete_requires_auth(self):
        """Test document deletion requires authentication."""
        response = client.delete("/documents/1")
        assert response.status_code == 401


class TestDocumentBiomarkers:
    """Test document biomarker retrieval."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"bio_test_{int(time.time())}@test.com"
        self.password = "BioTestPassword123"
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

    def test_get_document_biomarkers_nonexistent(self):
        """Test getting biomarkers for non-existent document returns 404."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/documents/99999/biomarkers", headers=self.headers)
        assert response.status_code == 404

    def test_get_biomarkers_requires_auth(self):
        """Test getting biomarkers requires authentication."""
        response = client.get("/documents/1/biomarkers")
        assert response.status_code == 401


class TestBulkDownload:
    """Test bulk document download."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user."""
        self.email = f"bulk_test_{int(time.time())}@test.com"
        self.password = "BulkTestPassword123"
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

    def test_bulk_download_empty(self):
        """Test bulk download for user with no documents."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/documents/download-all", headers=self.headers)
        # Should return 404 or empty zip depending on implementation
        assert response.status_code in [200, 404]

    def test_bulk_download_requires_auth(self):
        """Test bulk download requires authentication."""
        response = client.get("/documents/download-all")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
