"""
Bug Reporter Module - Automatically logs detected bugs to BUGS.md

This module parses test failures and creates/updates entries in BUGS.md
with proper formatting, deduplication, and severity classification.
"""

import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class BugReport:
    """Represents a single bug report."""

    def __init__(
        self,
        test_name: str,
        description: str,
        expected: str,
        actual: str,
        severity: str = "Medium",
        category: str = "Data Consistency",
        reproduction_steps: Optional[List[str]] = None
    ):
        self.test_name = test_name
        self.description = description
        self.expected = expected
        self.actual = actual
        self.severity = severity
        self.category = category
        self.reproduction_steps = reproduction_steps or []
        self.detected_at = datetime.now()
        self.bug_id = self._generate_bug_id()

    def _generate_bug_id(self) -> str:
        """Generate a unique bug ID based on test name."""
        hash_input = f"{self.test_name}:{self.category}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
        return f"AUTO-{short_hash}"

    def to_markdown(self) -> str:
        """Convert bug report to markdown format."""
        lines = [
            f"### {self.bug_id}: [AUTO-DETECTED] {self._short_description()}",
            f"**Detected:** {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Test:** `{self.test_name}`",
            f"**Status:** New",
            f"**Severity:** {self.severity}",
            f"**Category:** {self.category}",
            "",
            "**Description:**",
            self.description,
            "",
            "**Expected:**",
            self.expected,
            "",
            "**Actual:**",
            self.actual,
        ]

        if self.reproduction_steps:
            lines.extend([
                "",
                "**Reproduction:**",
            ])
            for i, step in enumerate(self.reproduction_steps, 1):
                lines.append(f"{i}. {step}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _short_description(self) -> str:
        """Generate a short description from the full description."""
        # Take first sentence or first 80 chars
        first_sentence = self.description.split('.')[0]
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence


class BugReporter:
    """Manages bug reporting to BUGS.md file."""

    AUTO_DETECTED_SECTION = "## Auto-Detected Bugs"

    def __init__(self, bugs_file: Optional[str] = None):
        if bugs_file:
            self.bugs_file = Path(bugs_file)
        else:
            # Find BUGS.md relative to project root
            self.bugs_file = self._find_bugs_file()

    def _find_bugs_file(self) -> Path:
        """Find BUGS.md in the project root."""
        # Start from this file's location and go up to find BUGS.md
        current = Path(__file__).resolve()
        for _ in range(5):  # Go up max 5 levels
            current = current.parent
            bugs_path = current / "BUGS.md"
            if bugs_path.exists():
                return bugs_path
        # Default to project root assumption
        return Path(__file__).resolve().parent.parent.parent / "BUGS.md"

    def _read_bugs_file(self) -> str:
        """Read the current BUGS.md content."""
        if self.bugs_file.exists():
            return self.bugs_file.read_text(encoding='utf-8')
        return ""

    def _get_existing_bug_ids(self, content: str) -> set:
        """Extract existing bug IDs from BUGS.md."""
        # Match both manual (BUG-XXX) and auto-detected (AUTO-XXXXXX) IDs
        pattern = r'### (BUG-\d+|AUTO-[A-F0-9]+):'
        matches = re.findall(pattern, content)
        return set(matches)

    def _ensure_auto_section_exists(self, content: str) -> str:
        """Ensure the auto-detected bugs section exists in BUGS.md."""
        if self.AUTO_DETECTED_SECTION not in content:
            # Add section before "## Deployment Notes" or at the end
            if "## Deployment Notes" in content:
                content = content.replace(
                    "## Deployment Notes",
                    f"{self.AUTO_DETECTED_SECTION}\n\n(No auto-detected bugs yet)\n\n---\n\n## Deployment Notes"
                )
            else:
                content += f"\n\n{self.AUTO_DETECTED_SECTION}\n\n(No auto-detected bugs yet)\n"
        return content

    def report_bug(self, bug: BugReport) -> bool:
        """
        Report a bug to BUGS.md.

        Returns True if bug was added, False if it already exists.
        """
        content = self._read_bugs_file()
        existing_ids = self._get_existing_bug_ids(content)

        # Check for duplicate
        if bug.bug_id in existing_ids:
            print(f"Bug {bug.bug_id} already exists, skipping.")
            return False

        # Ensure auto-detected section exists
        content = self._ensure_auto_section_exists(content)

        # Add bug to auto-detected section
        bug_markdown = bug.to_markdown()

        # Replace the placeholder or append to section
        if "(No auto-detected bugs yet)" in content:
            content = content.replace(
                "(No auto-detected bugs yet)",
                bug_markdown
            )
        else:
            # Find the auto-detected section and append
            section_start = content.find(self.AUTO_DETECTED_SECTION)
            if section_start != -1:
                # Find the next section or end
                next_section = content.find("\n## ", section_start + len(self.AUTO_DETECTED_SECTION))
                if next_section == -1:
                    # Append at end
                    content = content.rstrip() + "\n\n" + bug_markdown
                else:
                    # Insert before next section
                    content = content[:next_section] + bug_markdown + "\n" + content[next_section:]

        # Write back
        self.bugs_file.write_text(content, encoding='utf-8')
        print(f"Reported bug {bug.bug_id}: {bug._short_description()}")
        return True

    def report_bugs(self, bugs: List[BugReport]) -> Dict[str, Any]:
        """
        Report multiple bugs.

        Returns a summary dict with counts.
        """
        added = 0
        skipped = 0

        for bug in bugs:
            if self.report_bug(bug):
                added += 1
            else:
                skipped += 1

        return {
            "total": len(bugs),
            "added": added,
            "skipped": skipped
        }

    def clear_auto_detected(self):
        """Clear all auto-detected bugs (for testing/reset)."""
        content = self._read_bugs_file()

        # Find and clear the auto-detected section
        section_start = content.find(self.AUTO_DETECTED_SECTION)
        if section_start == -1:
            return

        next_section = content.find("\n## ", section_start + len(self.AUTO_DETECTED_SECTION))

        if next_section == -1:
            # Section is at end, clear everything after header
            content = content[:section_start + len(self.AUTO_DETECTED_SECTION)] + "\n\n(No auto-detected bugs yet)\n"
        else:
            # Clear between sections
            content = (
                content[:section_start + len(self.AUTO_DETECTED_SECTION)] +
                "\n\n(No auto-detected bugs yet)\n\n---\n" +
                content[next_section:]
            )

        self.bugs_file.write_text(content, encoding='utf-8')
        print("Cleared all auto-detected bugs.")


def create_bug_from_test_failure(
    test_name: str,
    error_message: str,
    expected: str = "",
    actual: str = "",
    category: str = "Data Consistency"
) -> BugReport:
    """Helper to create a BugReport from a test failure."""
    # Try to extract expected/actual from assertion error
    if not expected and not actual:
        if "assert" in error_message.lower():
            parts = error_message.split("==")
            if len(parts) == 2:
                expected = parts[1].strip()
                actual = parts[0].split("assert")[-1].strip()

    return BugReport(
        test_name=test_name,
        description=error_message,
        expected=expected or "See test for expected behavior",
        actual=actual or "See error message",
        category=category
    )
