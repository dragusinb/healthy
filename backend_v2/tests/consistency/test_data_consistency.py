"""
Data Consistency Tests

Tests that verify data consistency across different API endpoints.
These catch bugs like the biomarker count mismatch (BUG-001).

Can run against:
- Live production API (read-only, with --target live)
- Test database (with --target test)
"""

import pytest
from typing import Optional

from backend_v2.tests.bug_reporter import BugReport, BugReporter


class TestBiomarkerConsistency:
    """Tests for biomarker data consistency across endpoints."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_biomarker_count_matches_grouped(self, authenticated_live_client, bugs_reporter):
        """
        Dashboard stats biomarker count should match grouped biomarkers count.

        This catches BUG-001 type issues where different endpoints show
        different counts for the same underlying data.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get stats count
        stats_response = authenticated_live_client.get("/dashboard/stats")
        assert stats_response.status_code == 200, f"Stats endpoint failed: {stats_response.text}"
        stats = stats_response.json()
        stats_count = stats.get("biomarkers_count", 0)

        # Get grouped biomarkers count
        grouped_response = authenticated_live_client.get("/dashboard/biomarkers-grouped")
        assert grouped_response.status_code == 200, f"Grouped endpoint failed: {grouped_response.text}"
        grouped = grouped_response.json()
        grouped_count = len(grouped)

        # Compare
        if stats_count != grouped_count:
            bug = BugReport(
                test_name="test_data_consistency::test_biomarker_count_matches_grouped",
                description=f"Dashboard stats biomarker count ({stats_count}) does not match grouped biomarkers count ({grouped_count}).",
                expected=f"Both endpoints should return the same count: {grouped_count} unique biomarkers",
                actual=f"/dashboard/stats returns {stats_count}, /dashboard/biomarkers-grouped returns {grouped_count}",
                severity="Medium",
                category="Data Consistency",
                reproduction_steps=[
                    "GET /dashboard/stats",
                    "GET /dashboard/biomarkers-grouped",
                    "Compare biomarkers_count with len(response)"
                ]
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Biomarker count mismatch: stats={stats_count}, grouped={grouped_count}")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_alerts_count_consistency(self, authenticated_live_client, bugs_reporter):
        """
        Alert count should be consistent with filtered biomarkers.

        Note: alerts_count counts individual abnormal records, not unique biomarkers.
        This test verifies the count logic is correct.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get alerts count
        alerts_response = authenticated_live_client.get("/dashboard/alerts-count")
        assert alerts_response.status_code == 200
        alerts_count = alerts_response.json().get("alerts_count", 0)

        # Get all biomarkers and count abnormal ones
        biomarkers_response = authenticated_live_client.get("/dashboard/biomarkers")
        assert biomarkers_response.status_code == 200
        biomarkers = biomarkers_response.json()

        # Count abnormal biomarkers (status != "normal")
        abnormal_count = sum(1 for b in biomarkers if b.get("status") != "normal")

        if alerts_count != abnormal_count:
            bug = BugReport(
                test_name="test_data_consistency::test_alerts_count_consistency",
                description=f"Alerts count ({alerts_count}) does not match abnormal biomarkers count ({abnormal_count}).",
                expected=f"alerts_count should equal count of biomarkers with status != 'normal'",
                actual=f"/dashboard/alerts-count returns {alerts_count}, manual count shows {abnormal_count}",
                severity="Low",
                category="Data Consistency",
                reproduction_steps=[
                    "GET /dashboard/alerts-count",
                    "GET /dashboard/biomarkers",
                    "Count biomarkers where status != 'normal'"
                ]
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Alert count mismatch: endpoint={alerts_count}, calculated={abnormal_count}")

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_recent_biomarkers_are_subset(self, authenticated_live_client, bugs_reporter):
        """
        Recent biomarkers should be a subset of all biomarkers.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get recent biomarkers
        recent_response = authenticated_live_client.get("/dashboard/recent-biomarkers?limit=10")
        assert recent_response.status_code == 200
        recent = recent_response.json()
        recent_names = {b.get("name") for b in recent}

        # Get grouped biomarkers (all unique)
        grouped_response = authenticated_live_client.get("/dashboard/biomarkers-grouped")
        assert grouped_response.status_code == 200
        grouped = grouped_response.json()
        all_names = {b.get("canonical_name") for b in grouped}

        # Check recent is subset of all
        missing = recent_names - all_names
        if missing:
            bug = BugReport(
                test_name="test_data_consistency::test_recent_biomarkers_are_subset",
                description=f"Recent biomarkers contain names not in all biomarkers: {missing}",
                expected="All recent biomarker names should exist in the full biomarkers list",
                actual=f"Missing from full list: {missing}",
                severity="Medium",
                category="Data Consistency"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Recent biomarkers not subset of all: {missing}")


class TestDocumentConsistency:
    """Tests for document data consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_document_count_consistency(self, authenticated_live_client, bugs_reporter):
        """
        Document stats should match document list count.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get stats
        stats_response = authenticated_live_client.get("/dashboard/stats")
        assert stats_response.status_code == 200
        stats_count = stats_response.json().get("documents_count", 0)

        # Get document list (first page)
        # Note: This assumes all docs fit in one page or we'd need pagination
        docs_response = authenticated_live_client.get("/documents/?limit=1000")
        assert docs_response.status_code == 200
        docs = docs_response.json()
        docs_count = len(docs.get("documents", docs)) if isinstance(docs, dict) else len(docs)

        if stats_count != docs_count:
            bug = BugReport(
                test_name="test_data_consistency::test_document_count_consistency",
                description=f"Dashboard document count ({stats_count}) doesn't match document list ({docs_count}).",
                expected="Both should return the same count",
                actual=f"/dashboard/stats: {stats_count}, /documents/: {docs_count}",
                severity="Medium",
                category="Data Consistency"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Document count mismatch: stats={stats_count}, list={docs_count}")


class TestProfileConsistency:
    """Tests for user profile data consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_profile_data_matches_user_me(self, authenticated_live_client, bugs_reporter):
        """
        Profile data from /users/me should match /users/profile.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get user/me
        me_response = authenticated_live_client.get("/users/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        me_profile = me_data.get("profile", {})

        # Get profile directly
        profile_response = authenticated_live_client.get("/users/profile")
        assert profile_response.status_code == 200
        profile_data = profile_response.json()

        # Compare key fields
        fields_to_compare = ["full_name", "date_of_birth", "gender", "blood_type"]
        mismatches = []

        for field in fields_to_compare:
            me_value = me_profile.get(field)
            profile_value = profile_data.get(field)
            if me_value != profile_value:
                mismatches.append(f"{field}: /users/me={me_value}, /users/profile={profile_value}")

        if mismatches:
            bug = BugReport(
                test_name="test_data_consistency::test_profile_data_matches_user_me",
                description=f"Profile data mismatch between endpoints: {'; '.join(mismatches)}",
                expected="Both endpoints should return identical profile data",
                actual="\n".join(mismatches),
                severity="High",
                category="Data Consistency"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Profile mismatch: {mismatches}")


class TestHealthReportConsistency:
    """Tests for health report data consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_latest_report_in_reports_list(self, authenticated_live_client, bugs_reporter):
        """
        Latest report should appear in reports list.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get latest report
        latest_response = authenticated_live_client.get("/health/latest")
        if latest_response.status_code != 200:
            pytest.skip("No health reports available")

        latest = latest_response.json()
        if not latest.get("has_report"):
            pytest.skip("No health reports available")

        latest_id = latest.get("id")

        # Get reports list
        reports_response = authenticated_live_client.get("/health/reports?limit=50")
        assert reports_response.status_code == 200
        reports = reports_response.json()

        report_ids = {r.get("id") for r in reports}

        if latest_id not in report_ids:
            bug = BugReport(
                test_name="test_data_consistency::test_latest_report_in_reports_list",
                description=f"Latest report (id={latest_id}) not found in reports list.",
                expected="Latest report should be included in the reports list",
                actual=f"Report {latest_id} missing from list of {len(reports)} reports",
                severity="Medium",
                category="Data Consistency"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Latest report {latest_id} not in reports list")


class TestPatientInfoConsistency:
    """Tests for patient information consistency."""

    @pytest.mark.live_api
    @pytest.mark.requires_vault
    def test_patient_count_matches_documents(self, authenticated_live_client, bugs_reporter):
        """
        Patient info should be consistent with document patient data.
        """
        if not authenticated_live_client:
            pytest.skip("No authenticated client available")

        # Get patient info
        patient_response = authenticated_live_client.get("/dashboard/patient-info")
        assert patient_response.status_code == 200
        patient_info = patient_response.json()

        total_docs = patient_info.get("total_documents", 0)
        unknown_docs = patient_info.get("unknown_patient_documents", 0)
        patient_docs_sum = sum(patient_info.get("patient_documents", {}).values())

        # Verify: patient_docs + unknown = total
        calculated_total = patient_docs_sum + unknown_docs
        if calculated_total != total_docs:
            bug = BugReport(
                test_name="test_data_consistency::test_patient_count_matches_documents",
                description=f"Patient document counts don't add up: {patient_docs_sum} + {unknown_docs} != {total_docs}",
                expected=f"patient_docs + unknown_patient_docs should equal total_documents",
                actual=f"{patient_docs_sum} + {unknown_docs} = {calculated_total}, but total is {total_docs}",
                severity="Low",
                category="Data Consistency"
            )
            bugs_reporter.report_bug(bug)
            pytest.fail(f"Patient document count mismatch")
