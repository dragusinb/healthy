"""
Vault Integrity Tests

Tests that verify the vault encryption system is working correctly
and data integrity is maintained through encrypt/decrypt cycles.
"""

import pytest
from backend_v2.tests.bug_reporter import BugReport, BugReporter


class TestVaultStatus:
    """Tests for vault status and availability."""

    @pytest.mark.live_api
    def test_vault_status_endpoint_available(self, live_api_client, bugs_reporter):
        """
        Vault status endpoint should always be available.
        """
        response = live_api_client.get("/admin/vault/status")

        if response.status_code != 200:
            bug = BugReport(
                test_name="test_vault_integrity::test_vault_status_endpoint_available",
                description=f"Vault status endpoint returned {response.status_code} instead of 200.",
                expected="Vault status endpoint should always return 200",
                actual=f"Status code: {response.status_code}, Response: {response.text}",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Vault status endpoint failed: {response.status_code}")

        data = response.json()
        assert "is_unlocked" in data, "Response should contain is_unlocked"
        assert "is_configured" in data, "Response should contain is_configured"

    @pytest.mark.live_api
    def test_vault_is_configured(self, live_api_client, bugs_reporter):
        """
        Vault should be configured in production.
        """
        response = live_api_client.get("/admin/vault/status")
        assert response.status_code == 200

        data = response.json()
        if not data.get("is_configured"):
            bug = BugReport(
                test_name="test_vault_integrity::test_vault_is_configured",
                description="Vault is not configured on production server.",
                expected="Vault should be initialized with master password",
                actual="is_configured = False",
                severity="Critical",
                category="Vault Integrity",
                reproduction_steps=[
                    "GET /admin/vault/status",
                    "Check is_configured field"
                ]
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Vault not configured")

    @pytest.mark.live_api
    def test_vault_is_unlocked(self, live_api_client, bugs_reporter):
        """
        Vault should be unlocked for normal operation.
        """
        response = live_api_client.get("/admin/vault/status")
        assert response.status_code == 200

        data = response.json()
        if not data.get("is_unlocked"):
            bug = BugReport(
                test_name="test_vault_integrity::test_vault_is_unlocked",
                description="Vault is locked. Encrypted data is inaccessible.",
                expected="Vault should be unlocked after server restart",
                actual="is_unlocked = False - all encrypted data inaccessible",
                severity="Critical",
                category="Vault Integrity",
                reproduction_steps=[
                    "GET /admin/vault/status",
                    "Check is_unlocked field",
                    "If locked, POST /admin/vault/unlock with master password"
                ]
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Vault is locked")


class TestDataDecryption:
    """Tests that verify data can be decrypted correctly."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_biomarkers_have_values(self, authenticated_live_client, bugs_reporter):
        """
        Biomarkers should have decrypted values (not null/empty).
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        response = authenticated_live_client.get("/dashboard/biomarkers?limit=50")
        if response.status_code != 200:
            pytest.skip("Could not fetch biomarkers")

        biomarkers = response.json()
        if not biomarkers:
            pytest.skip("No biomarkers to test")

        # Check for null/empty values that might indicate decryption failure
        null_value_count = 0
        for b in biomarkers[:50]:  # Check first 50
            value = b.get("value")
            if value is None or value == "" or value == "null":
                null_value_count += 1

        # Allow some null values (some biomarkers legitimately don't have numeric values)
        # But if more than 50% are null, something is wrong
        if null_value_count > len(biomarkers[:50]) * 0.5:
            bug = BugReport(
                test_name="test_vault_integrity::test_biomarkers_have_values",
                description=f"Too many biomarkers have null/empty values ({null_value_count}/{len(biomarkers[:50])}). Possible decryption failure.",
                expected="Most biomarkers should have valid decrypted values",
                actual=f"{null_value_count} out of {len(biomarkers[:50])} biomarkers have null/empty values",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Too many null values: {null_value_count}/{len(biomarkers[:50])}")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_profile_data_decrypts(self, authenticated_live_client, bugs_reporter):
        """
        Profile data should decrypt without errors.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        response = authenticated_live_client.get("/users/profile")

        if response.status_code == 503:
            bug = BugReport(
                test_name="test_vault_integrity::test_profile_data_decrypts",
                description="Profile endpoint returned 503 - vault may be locked.",
                expected="Profile should be accessible when vault is unlocked",
                actual=f"503 response: {response.text}",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Profile inaccessible - vault locked")

        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_health_reports_decrypt(self, authenticated_live_client, bugs_reporter):
        """
        Health reports should have decrypted content.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        response = authenticated_live_client.get("/health/reports?limit=5")
        if response.status_code != 200:
            pytest.skip("Could not fetch reports")

        reports = response.json()
        if not reports:
            pytest.skip("No reports to test")

        # Check that reports have content
        empty_reports = []
        for r in reports:
            summary = r.get("summary", "")
            findings = r.get("findings", [])
            if not summary and not findings:
                empty_reports.append(r.get("id"))

        if empty_reports and len(empty_reports) == len(reports):
            bug = BugReport(
                test_name="test_vault_integrity::test_health_reports_decrypt",
                description=f"All health reports have empty content. Possible decryption failure.",
                expected="Reports should have summary and/or findings",
                actual=f"All {len(reports)} reports have empty content",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("All reports have empty content")


class TestEncryptionState:
    """Tests for encryption state consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_linked_accounts_accessible(self, authenticated_live_client, bugs_reporter):
        """
        Linked accounts should be accessible (usernames decrypted).
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        response = authenticated_live_client.get("/users/me")
        assert response.status_code == 200

        data = response.json()
        accounts = data.get("linked_accounts", [])

        # Check if any accounts have "[encrypted]" username
        encrypted_usernames = [
            a for a in accounts
            if a.get("username") == "[encrypted]"
        ]

        if encrypted_usernames and len(encrypted_usernames) == len(accounts) and len(accounts) > 0:
            bug = BugReport(
                test_name="test_vault_integrity::test_linked_accounts_accessible",
                description="All linked account usernames show '[encrypted]' - vault may be locked.",
                expected="Usernames should be decrypted when vault is unlocked",
                actual=f"All {len(accounts)} accounts show '[encrypted]' username",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Linked account usernames not decrypted")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_documents_downloadable(self, authenticated_live_client, bugs_reporter):
        """
        At least one document should be downloadable (decryptable).
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get document list
        docs_response = authenticated_live_client.get("/documents/?limit=5")
        if docs_response.status_code != 200:
            pytest.skip("Could not fetch documents")

        docs_data = docs_response.json()
        documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data

        if not documents:
            pytest.skip("No documents to test")

        # Try to download first document
        first_doc_id = documents[0].get("id")
        download_response = authenticated_live_client.get(f"/documents/{first_doc_id}/download")

        if download_response.status_code == 503:
            bug = BugReport(
                test_name="test_vault_integrity::test_documents_downloadable",
                description="Document download returned 503 - vault may be locked.",
                expected="Documents should be downloadable when vault is unlocked",
                actual=f"503 response for document {first_doc_id}",
                severity="High",
                category="Vault Integrity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Documents not downloadable - vault locked")

        # Check for valid PDF content
        if download_response.status_code == 200:
            content_type = download_response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
                bug = BugReport(
                    test_name="test_vault_integrity::test_documents_downloadable",
                    description=f"Document download returned unexpected content type: {content_type}",
                    expected="Content-Type should be application/pdf or octet-stream",
                    actual=f"Content-Type: {content_type}",
                    severity="Medium",
                    category="Vault Integrity"
                )
                bugs_reporter.report_bug(bug)
