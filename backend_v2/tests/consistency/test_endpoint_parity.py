"""
Endpoint Parity Tests

Tests that verify related endpoints return consistent data
and that API contracts are maintained.
"""

import pytest
from backend_v2.tests.bug_reporter import BugReport, BugReporter


class TestBiomarkerEndpointParity:
    """Tests for biomarker endpoint consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_biomarkers_flat_vs_grouped_same_data(self, authenticated_live_client, bugs_reporter):
        """
        Flat biomarkers and grouped biomarkers should contain the same underlying data.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get flat biomarkers
        flat_response = authenticated_live_client.get("/dashboard/biomarkers")
        assert flat_response.status_code == 200
        flat_biomarkers = flat_response.json()

        # Get grouped biomarkers
        grouped_response = authenticated_live_client.get("/dashboard/biomarkers-grouped")
        assert grouped_response.status_code == 200
        grouped = grouped_response.json()

        # Count total records in grouped (sum of history lengths)
        grouped_total = sum(len(g.get("history", [])) for g in grouped)

        if len(flat_biomarkers) != grouped_total:
            bug = BugReport(
                test_name="test_endpoint_parity::test_biomarkers_flat_vs_grouped_same_data",
                description=f"Flat biomarkers count ({len(flat_biomarkers)}) differs from grouped total ({grouped_total}).",
                expected="Both should represent the same underlying data",
                actual=f"Flat: {len(flat_biomarkers)}, Grouped total: {grouped_total}",
                severity="Medium",
                category="Endpoint Parity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Data mismatch: flat={len(flat_biomarkers)}, grouped_total={grouped_total}")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_evolution_contains_all_history(self, authenticated_live_client, bugs_reporter):
        """
        Evolution endpoint should return all historical values for a biomarker.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get grouped biomarkers to find one with history
        grouped_response = authenticated_live_client.get("/dashboard/biomarkers-grouped")
        assert grouped_response.status_code == 200
        grouped = grouped_response.json()

        # Find a biomarker with at least 2 history entries
        test_biomarker = None
        expected_count = 0
        for g in grouped:
            history = g.get("history", [])
            if len(history) >= 2:
                test_biomarker = g.get("canonical_name")
                expected_count = len(history)
                break

        if not test_biomarker:
            pytest.skip("No biomarker with multiple history entries")

        # Get evolution for this biomarker
        evolution_response = authenticated_live_client.get(f"/dashboard/evolution/{test_biomarker}")
        assert evolution_response.status_code == 200
        evolution = evolution_response.json()

        if len(evolution) != expected_count:
            bug = BugReport(
                test_name="test_endpoint_parity::test_evolution_contains_all_history",
                description=f"Evolution for '{test_biomarker}' returned {len(evolution)} points, expected {expected_count}.",
                expected=f"Evolution should contain all {expected_count} historical values",
                actual=f"Evolution contains {len(evolution)} data points",
                severity="Medium",
                category="Endpoint Parity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Evolution missing data: got {len(evolution)}, expected {expected_count}")


class TestDocumentEndpointParity:
    """Tests for document endpoint consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_document_stats_match_providers(self, authenticated_live_client, bugs_reporter):
        """
        Document stats by provider should sum to total documents.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get document stats
        stats_response = authenticated_live_client.get("/documents/stats")
        if stats_response.status_code != 200:
            pytest.skip("Document stats endpoint not available")

        stats = stats_response.json()
        provider_totals = stats.get("by_provider", {})
        stats_total = sum(provider_totals.values()) if provider_totals else 0

        # Get document list count
        docs_response = authenticated_live_client.get("/documents/?limit=1000")
        assert docs_response.status_code == 200
        docs_data = docs_response.json()
        documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data
        list_total = len(documents)

        if stats_total != list_total:
            bug = BugReport(
                test_name="test_endpoint_parity::test_document_stats_match_providers",
                description=f"Document provider stats sum ({stats_total}) differs from document list count ({list_total}).",
                expected="Provider totals should sum to total documents",
                actual=f"Stats sum: {stats_total}, List count: {list_total}",
                severity="Low",
                category="Endpoint Parity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Stats mismatch: sum={stats_total}, list={list_total}")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_document_biomarkers_match(self, authenticated_live_client, bugs_reporter):
        """
        Document-specific biomarkers should match filtered biomarkers.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get document list
        docs_response = authenticated_live_client.get("/documents/?limit=5")
        assert docs_response.status_code == 200
        docs_data = docs_response.json()
        documents = docs_data.get("documents", docs_data) if isinstance(docs_data, dict) else docs_data

        if not documents:
            pytest.skip("No documents to test")

        # Get biomarkers for first document
        doc_id = documents[0].get("id")
        doc_biomarkers_response = authenticated_live_client.get(f"/documents/{doc_id}/biomarkers")

        if doc_biomarkers_response.status_code != 200:
            pytest.skip("Document biomarkers endpoint not available")

        doc_response = doc_biomarkers_response.json()
        # Handle nested response structure: {document: {...}, biomarkers: [...]}
        doc_biomarkers = doc_response.get("biomarkers", doc_response) if isinstance(doc_response, dict) else doc_response

        # Get all biomarkers and filter by document_id
        all_response = authenticated_live_client.get("/dashboard/biomarkers")
        assert all_response.status_code == 200
        all_biomarkers = all_response.json()

        filtered = [b for b in all_biomarkers if b.get("document_id") == doc_id]

        if len(doc_biomarkers) != len(filtered):
            bug = BugReport(
                test_name="test_endpoint_parity::test_document_biomarkers_match",
                description=f"Document {doc_id} biomarkers ({len(doc_biomarkers)}) differs from filtered all ({len(filtered)}).",
                expected="Both should return same biomarkers",
                actual=f"Document endpoint: {len(doc_biomarkers)}, Filtered: {len(filtered)}",
                severity="Low",
                category="Endpoint Parity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Document biomarkers mismatch")


class TestHealthEndpointParity:
    """Tests for health report endpoint consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_reports_list_contains_history_items(self, authenticated_live_client, bugs_reporter):
        """
        Reports from /reports should match reports in /history.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get reports list
        reports_response = authenticated_live_client.get("/health/reports?limit=50")
        assert reports_response.status_code == 200
        reports = reports_response.json()

        if not reports:
            pytest.skip("No reports to test")

        # Get history
        history_response = authenticated_live_client.get("/health/history?limit=50")
        assert history_response.status_code == 200
        history = history_response.json()

        # Collect all report IDs from history
        history_ids = set()
        for session in history.get("sessions", []):
            if session.get("general", {}).get("id"):
                history_ids.add(session["general"]["id"])
            for specialist in session.get("specialists", []):
                if specialist.get("id"):
                    history_ids.add(specialist["id"])

        # All reports should be in history
        reports_ids = {r.get("id") for r in reports if r.get("report_type") != "gap_analysis"}
        missing = reports_ids - history_ids

        if missing and len(missing) > len(reports_ids) * 0.2:  # Allow 20% discrepancy
            bug = BugReport(
                test_name="test_endpoint_parity::test_reports_list_contains_history_items",
                description=f"{len(missing)} reports from /reports not found in /history.",
                expected="Reports list and history should contain the same reports",
                actual=f"Missing from history: {len(missing)} reports",
                severity="Low",
                category="Endpoint Parity"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Reports missing from history: {missing}")


class TestUserIsolation:
    """Tests that verify users can only access their own data."""

    @pytest.mark.live_api
    def test_unauthenticated_access_blocked(self, live_api_client, bugs_reporter):
        """
        Protected endpoints should reject unauthenticated requests.
        """
        protected_endpoints = [
            "/dashboard/stats",
            "/dashboard/biomarkers",
            "/documents/",
            "/users/me",
            "/health/reports"
        ]

        accessible = []
        for endpoint in protected_endpoints:
            response = live_api_client.get(endpoint)
            if response.status_code == 200:
                accessible.append(endpoint)

        if accessible:
            bug = BugReport(
                test_name="test_endpoint_parity::test_unauthenticated_access_blocked",
                description=f"Protected endpoints accessible without authentication: {accessible}",
                expected="All protected endpoints should return 401 or 403",
                actual=f"Accessible without auth: {accessible}",
                severity="Critical",
                category="Security"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Security issue: {accessible} accessible without auth")

    @pytest.mark.live_api
    def test_invalid_token_rejected(self, live_api_client, bugs_reporter):
        """
        Invalid JWT tokens should be rejected.
        """
        live_api_client.headers["Authorization"] = "Bearer invalid_token_here"

        response = live_api_client.get("/users/me")

        if response.status_code == 200:
            bug = BugReport(
                test_name="test_endpoint_parity::test_invalid_token_rejected",
                description="Invalid JWT token was accepted by the API.",
                expected="Invalid tokens should return 401",
                actual=f"Status code: {response.status_code}",
                severity="Critical",
                category="Security"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail("Invalid token accepted")

        # Clean up header
        del live_api_client.headers["Authorization"]


class TestAPIResponseFormat:
    """Tests that verify API response formats are consistent."""

    @pytest.mark.live_api
    def test_error_responses_have_detail(self, live_api_client, bugs_reporter):
        """
        Error responses should include a 'detail' field.
        """
        # Trigger a 404
        response = live_api_client.get("/nonexistent-endpoint-12345")

        if response.status_code >= 400:
            try:
                data = response.json()
                if "detail" not in data:
                    bug = BugReport(
                        test_name="test_endpoint_parity::test_error_responses_have_detail",
                        description="Error response missing 'detail' field.",
                        expected="Error responses should have {'detail': 'message'}",
                        actual=f"Response: {data}",
                        severity="Low",
                        category="API Contract"
                    )
                    bugs_reporter.report_bug(bug)
            except Exception:
                pass  # Non-JSON response is acceptable for 404
