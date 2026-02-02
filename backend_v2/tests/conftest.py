"""
Shared pytest fixtures for the Healthy test suite.

Provides fixtures for:
- Test database setup
- API clients (test and live)
- Authentication helpers
- Test data seeding
"""

import os
import sys
import pytest
import httpx
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["ENVIRONMENT"] = "test"


# ============================================================================
# Configuration
# ============================================================================

LIVE_API_URL = os.getenv("LIVE_API_URL", "https://analize.online/api")
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "http://localhost:8000")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def live_api_client():
    """
    HTTP client for testing against the live production API.

    IMPORTANT: Only use for read-only tests!
    This client connects to the real production server.
    """
    with httpx.Client(base_url=LIVE_API_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def local_api_client():
    """HTTP client for testing against local development server."""
    with httpx.Client(base_url=LOCAL_API_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def authenticated_live_client(live_api_client):
    """
    Authenticated client for live API testing.

    Uses test credentials from environment variables.
    Returns None if authentication fails (no test user on production).
    """
    try:
        response = live_api_client.post(
            "/auth/token",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            live_api_client.headers["Authorization"] = f"Bearer {token}"
            return live_api_client
    except Exception:
        pass
    return None


# ============================================================================
# Test Database Fixtures (for isolated testing)
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    from sqlalchemy import create_engine

    test_db_path = Path(__file__).parent / "test_consistency.db"
    engine = create_engine(f"sqlite:///{test_db_path}")

    yield engine

    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture(scope="session")
def test_db_tables(test_db_engine):
    """Create all tables in the test database."""
    from backend_v2.models import Base
    Base.metadata.create_all(bind=test_db_engine)
    yield
    Base.metadata.drop_all(bind=test_db_engine)


@pytest.fixture
def test_db_session(test_db_engine, test_db_tables):
    """Provide a database session for tests."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_biomarker_data():
    """Sample biomarker data for testing."""
    return [
        {
            "test_name": "Glucose",
            "canonical_name": "Glucose",
            "value": "95",
            "numeric_value": 95.0,
            "unit": "mg/dL",
            "reference_range": "70-100",
            "flags": "NORMAL"
        },
        {
            "test_name": "Cholesterol Total",
            "canonical_name": "Cholesterol Total",
            "value": "220",
            "numeric_value": 220.0,
            "unit": "mg/dL",
            "reference_range": "<200",
            "flags": "HIGH"
        },
        {
            "test_name": "Hemoglobin",
            "canonical_name": "Hemoglobin",
            "value": "14.5",
            "numeric_value": 14.5,
            "unit": "g/dL",
            "reference_range": "12-16",
            "flags": "NORMAL"
        },
    ]


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "consistency_test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "date_of_birth": "1990-01-01",
        "gender": "male"
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def bugs_reporter():
    """Provide a BugReporter instance for tests."""
    from backend_v2.tests.bug_reporter import BugReporter
    return BugReporter()


@pytest.fixture
def vault_status(live_api_client):
    """Check and return vault status."""
    try:
        response = live_api_client.get("/admin/vault/status")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"is_unlocked": False, "is_configured": False}


# ============================================================================
# Skip Conditions
# ============================================================================

def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "live_api: mark test as requiring live API access"
    )
    config.addinivalue_line(
        "markers", "requires_auth: mark test as requiring authentication"
    )
    config.addinivalue_line(
        "markers", "requires_vault: mark test as requiring unlocked vault"
    )


@pytest.fixture(autouse=True)
def skip_if_no_live_api(request, live_api_client):
    """Skip tests marked with 'live_api' if live API is unavailable."""
    if request.node.get_closest_marker('live_api'):
        try:
            response = live_api_client.get("/admin/vault/status")
            if response.status_code != 200:
                pytest.skip("Live API unavailable")
        except Exception as e:
            pytest.skip(f"Live API unavailable: {e}")


@pytest.fixture(autouse=True)
def skip_if_vault_locked(request, vault_status):
    """Skip tests marked with 'requires_vault' if vault is locked."""
    if request.node.get_closest_marker('requires_vault'):
        if not vault_status.get("is_unlocked"):
            pytest.skip("Vault is locked")
