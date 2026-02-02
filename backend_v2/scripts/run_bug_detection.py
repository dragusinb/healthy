#!/usr/bin/env python
"""
Bug Detection Runner

Runs automated bug detection tests and reports findings to BUGS.md.

Usage:
    python -m backend_v2.scripts.run_bug_detection --target live
    python -m backend_v2.scripts.run_bug_detection --target test
    python -m backend_v2.scripts.run_bug_detection --target live --report-bugs
    python -m backend_v2.scripts.run_bug_detection --target live --post-deploy

Arguments:
    --target: Where to run tests (live, test, local)
    --report-bugs: Automatically report failures to BUGS.md
    --post-deploy: Run in post-deployment mode (stricter, fails on any issue)
    --verbose: Show detailed output
    --dry-run: Show what would be reported without writing to BUGS.md
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def parse_args():
    parser = argparse.ArgumentParser(description="Run automated bug detection tests")
    parser.add_argument(
        "--target",
        choices=["live", "test", "local"],
        default="test",
        help="API target: live (production), test (test DB), local (localhost)"
    )
    parser.add_argument(
        "--report-bugs",
        action="store_true",
        help="Report detected bugs to BUGS.md"
    )
    parser.add_argument(
        "--post-deploy",
        action="store_true",
        help="Post-deployment mode: stricter checks, non-zero exit on any failure"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be reported without writing"
    )
    return parser.parse_args()


def setup_environment(target: str):
    """Set environment variables based on target."""
    if target == "live":
        os.environ["LIVE_API_URL"] = os.getenv("LIVE_API_URL", "https://analize.online/api")
    elif target == "local":
        os.environ["LIVE_API_URL"] = "http://localhost:8000"
    # test target uses default test database


def run_pytest(verbose: bool = False, post_deploy: bool = False) -> tuple:
    """
    Run pytest on consistency tests.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    tests_dir = project_root / "backend_v2" / "tests" / "consistency"

    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "--tb=short",
        "-q" if not verbose else "-v",
    ]

    if post_deploy:
        # In post-deploy mode, fail fast
        cmd.append("-x")

    # Capture output
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )

    return result.returncode, result.stdout, result.stderr


def parse_test_failures(stdout: str, stderr: str) -> list:
    """Parse pytest output to extract failure information."""
    failures = []

    # Simple parsing - look for FAILED lines
    for line in stdout.split('\n'):
        if 'FAILED' in line:
            # Format: FAILED test_file.py::TestClass::test_name - reason
            parts = line.split(' - ', 1)
            test_path = parts[0].replace('FAILED ', '').strip()
            reason = parts[1] if len(parts) > 1 else "Unknown failure"
            failures.append({
                "test": test_path,
                "reason": reason
            })

    return failures


def print_summary(return_code: int, failures: list, target: str):
    """Print a summary of the test run."""
    print("\n" + "=" * 60)
    print(f"Bug Detection Summary - Target: {target.upper()}")
    print("=" * 60)

    if return_code == 0:
        print("\n All consistency checks passed!")
    else:
        print(f"\n Found {len(failures)} potential issue(s):")
        for f in failures:
            print(f"  - {f['test']}")
            print(f"    Reason: {f['reason']}")

    print("\n" + "=" * 60)


def main():
    args = parse_args()

    print(f"\n{'=' * 60}")
    print(f"Healthy Bug Detection System")
    print(f"Target: {args.target}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    # Setup environment
    setup_environment(args.target)

    if args.dry_run:
        print("[DRY RUN] Would run tests but not write to BUGS.md\n")

    # Run tests
    print("Running consistency tests...\n")
    return_code, stdout, stderr = run_pytest(args.verbose, args.post_deploy)

    if args.verbose:
        print(stdout)
        if stderr:
            print("STDERR:", stderr)

    # Parse failures
    failures = parse_test_failures(stdout, stderr)

    # Print summary
    print_summary(return_code, failures, args.target)

    # Report bugs if requested
    if args.report_bugs and failures and not args.dry_run:
        print("\nReporting bugs to BUGS.md...")
        from backend_v2.tests.bug_reporter import BugReporter, BugReport

        reporter = BugReporter()
        for f in failures:
            # Create basic bug report from failure
            bug = BugReport(
                test_name=f["test"],
                description=f["reason"],
                expected="Test should pass",
                actual=f"Test failed: {f['reason']}",
                severity="Medium",
                category="Auto-Detected"
            )
            reporter.report_bug(bug)

    # Exit code
    if args.post_deploy and return_code != 0:
        print("\n POST-DEPLOY CHECK FAILED - Review issues above")
        sys.exit(1)

    sys.exit(return_code)


if __name__ == "__main__":
    main()
