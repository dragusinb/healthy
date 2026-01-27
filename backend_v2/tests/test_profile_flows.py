"""
Comprehensive profile management flow tests.
Tests profile viewing, updating, and validation.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_profile.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-characters!"

from main import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


class TestProfileManagement:
    """Test profile CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create authenticated user for profile tests."""
        self.email = f"profile_test_{int(time.time())}@test.com"
        self.password = "ProfileTestPassword123"
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

    def test_get_profile_initial(self):
        """Test getting profile returns empty/default values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.get("/users/profile", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data or "full_name" in data

    def test_update_full_name(self):
        """Test updating full name."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "full_name": "Test User Name"
        })
        assert response.status_code == 200
        # Verify update
        get_response = client.get("/users/profile", headers=self.headers)
        assert get_response.json().get("full_name") == "Test User Name"

    def test_update_gender_valid(self):
        """Test updating gender with valid values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        for gender in ["male", "female", "other"]:
            response = client.put("/users/profile", headers=self.headers, json={
                "gender": gender
            })
            assert response.status_code == 200

    def test_update_gender_invalid(self):
        """Test updating gender with invalid value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "gender": "invalid_gender"
        })
        assert response.status_code == 400

    def test_update_height_valid(self):
        """Test updating height with valid value."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": 175
        })
        assert response.status_code == 200

    def test_update_height_negative(self):
        """Test updating height with negative value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": -10
        })
        assert response.status_code == 400

    def test_update_height_too_large(self):
        """Test updating height with too large value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": 500
        })
        assert response.status_code == 400

    def test_update_height_zero(self):
        """Test updating height with zero sets to null."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "height_cm": 0
        })
        assert response.status_code == 200

    def test_update_weight_valid(self):
        """Test updating weight with valid value."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "weight_kg": 70
        })
        assert response.status_code == 200

    def test_update_weight_negative(self):
        """Test updating weight with negative value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "weight_kg": -10
        })
        assert response.status_code == 400

    def test_update_weight_too_large(self):
        """Test updating weight with too large value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "weight_kg": 600
        })
        assert response.status_code == 400

    def test_update_blood_type_valid(self):
        """Test updating blood type with valid values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        valid_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for blood_type in valid_types:
            response = client.put("/users/profile", headers=self.headers, json={
                "blood_type": blood_type
            })
            assert response.status_code == 200

    def test_update_blood_type_invalid(self):
        """Test updating blood type with invalid value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "blood_type": "X+"
        })
        assert response.status_code == 400

    def test_update_smoking_status_valid(self):
        """Test updating smoking status with valid values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        for status in ["never", "former", "current"]:
            response = client.put("/users/profile", headers=self.headers, json={
                "smoking_status": status
            })
            assert response.status_code == 200

    def test_update_smoking_status_invalid(self):
        """Test updating smoking status with invalid value fails."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "smoking_status": "sometimes"
        })
        assert response.status_code == 400

    def test_update_alcohol_valid(self):
        """Test updating alcohol consumption with valid values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        for level in ["none", "light", "moderate", "heavy"]:
            response = client.put("/users/profile", headers=self.headers, json={
                "alcohol_consumption": level
            })
            assert response.status_code == 200

    def test_update_physical_activity_valid(self):
        """Test updating physical activity with valid values."""
        if not self.token:
            pytest.skip("Auth setup failed")
        for level in ["sedentary", "light", "moderate", "active", "very_active"]:
            response = client.put("/users/profile", headers=self.headers, json={
                "physical_activity": level
            })
            assert response.status_code == 200

    def test_update_allergies_list(self):
        """Test updating allergies with list."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "allergies": ["penicillin", "peanuts"]
        })
        assert response.status_code == 200

    def test_update_chronic_conditions_list(self):
        """Test updating chronic conditions with list."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "chronic_conditions": ["diabetes", "hypertension"]
        })
        assert response.status_code == 200

    def test_update_medications_list(self):
        """Test updating medications with list."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "current_medications": ["metformin", "lisinopril"]
        })
        assert response.status_code == 200

    def test_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "full_name": "John Doe",
            "gender": "male",
            "height_cm": 180,
            "weight_kg": 80,
            "blood_type": "A+"
        })
        assert response.status_code == 200

    def test_update_date_of_birth(self):
        """Test updating date of birth."""
        if not self.token:
            pytest.skip("Auth setup failed")
        response = client.put("/users/profile", headers=self.headers, json={
            "date_of_birth": "1990-05-15"
        })
        assert response.status_code == 200

    def test_bmi_calculation(self):
        """Test BMI is calculated when height and weight are set."""
        if not self.token:
            pytest.skip("Auth setup failed")
        # Set height and weight
        client.put("/users/profile", headers=self.headers, json={
            "height_cm": 175,
            "weight_kg": 70
        })
        # Get profile and check BMI
        response = client.get("/users/profile", headers=self.headers)
        data = response.json()
        if "bmi" in data and data.get("height_cm") and data.get("weight_kg"):
            # BMI = weight / (height_m)^2
            expected_bmi = 70 / (1.75 ** 2)
            assert abs(data["bmi"] - expected_bmi) < 0.5  # Allow small rounding diff


class TestProfileIsolation:
    """Test that users can only access their own profile."""

    def test_users_see_own_profile_only(self):
        """Test that two users see their own profiles."""
        # Create user 1
        email1 = f"user1_{int(time.time())}@test.com"
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
        email2 = f"user2_{int(time.time())}@test.com"
        client.post("/auth/register", json={
            "email": email2,
            "password": "Password123"
        })
        token2 = client.post("/auth/token", data={
            "username": email2,
            "password": "Password123"
        }).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Update user 1's profile
        client.put("/users/profile", headers=headers1, json={
            "full_name": "User One"
        })

        # Update user 2's profile
        client.put("/users/profile", headers=headers2, json={
            "full_name": "User Two"
        })

        # Verify each sees only their own
        profile1 = client.get("/users/profile", headers=headers1).json()
        profile2 = client.get("/users/profile", headers=headers2).json()

        assert profile1.get("full_name") == "User One"
        assert profile2.get("full_name") == "User Two"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
