#!/usr/bin/env python3
"""
Test script for Synevo and Regina Maria crawlers.

Usage:
    python -m backend_v2.test_crawlers --provider synevo --username YOUR_CNP --password YOUR_PASSWORD
    python -m backend_v2.test_crawlers --provider regina --username YOUR_EMAIL --password YOUR_PASSWORD

Note:
    - For Regina Maria, reCAPTCHA may appear. The browser will open in visible mode
      so you can solve it manually. The crawler will wait up to 3 minutes.
    - For Synevo, the username is your CNP (Romanian ID number).
"""

import asyncio
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_v2.services.crawlers_manager import run_regina_async, run_synevo_async


async def test_synevo(username: str, password: str, headless: bool = False):
    """Test Synevo crawler."""
    print(f"\n{'='*60}")
    print("Testing Synevo Crawler")
    print(f"{'='*60}")
    print(f"Username (CNP): {username[:4]}...{username[-4:]}")
    print(f"Headless mode: {headless}")
    print(f"{'='*60}\n")

    result = await run_synevo_async(username, password, headless=headless)

    print(f"\n{'='*60}")
    print("RESULT:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if result['status'] == 'success' and 'documents' in result:
        print(f"\nDownloaded documents:")
        for doc in result['documents']:
            print(f"  - {doc['filename']}")
    print(f"{'='*60}\n")

    return result


async def test_regina(username: str, password: str, headless: bool = False):
    """Test Regina Maria crawler."""
    print(f"\n{'='*60}")
    print("Testing Regina Maria Crawler")
    print(f"{'='*60}")
    print(f"Username: {username}")
    print(f"Headless mode: {headless}")
    print(f"{'='*60}")
    print("\nNOTE: If reCAPTCHA appears, please solve it manually in the browser window.")
    print("The crawler will wait up to 3 minutes for you to complete it.\n")

    result = await run_regina_async(username, password, headless=headless)

    print(f"\n{'='*60}")
    print("RESULT:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if result['status'] == 'success' and 'documents' in result:
        print(f"\nDownloaded documents:")
        for doc in result['documents']:
            print(f"  - {doc['filename']}")
    print(f"{'='*60}\n")

    return result


async def main():
    parser = argparse.ArgumentParser(description="Test medical document crawlers")
    parser.add_argument("--provider", "-p", required=True, choices=["synevo", "regina", "both"],
                        help="Provider to test: synevo, regina, or both")
    parser.add_argument("--username", "-u", required=True,
                        help="Username (email for Regina Maria, CNP for Synevo)")
    parser.add_argument("--password", "-pw", required=True,
                        help="Password for the account")
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode (not recommended for Regina Maria due to reCAPTCHA)")

    # For testing both providers with different credentials
    parser.add_argument("--synevo-username", help="Synevo username (CNP) if different")
    parser.add_argument("--synevo-password", help="Synevo password if different")

    args = parser.parse_args()

    results = {}

    if args.provider in ["synevo", "both"]:
        synevo_user = args.synevo_username or args.username
        synevo_pass = args.synevo_password or args.password
        results["synevo"] = await test_synevo(synevo_user, synevo_pass, args.headless)

    if args.provider in ["regina", "both"]:
        results["regina"] = await test_regina(args.username, args.password, args.headless)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for provider, result in results.items():
        status_icon = "OK" if result["status"] == "success" else "FAILED"
        doc_count = len(result.get("documents", []))
        print(f"{provider.upper()}: [{status_icon}] - {doc_count} documents")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Install playwright browsers if needed
    print("Checking Playwright installation...")
    try:
        import playwright
        print("Playwright is installed.")
    except ImportError:
        print("Installing playwright...")
        os.system("pip install playwright")
        print("Installing playwright browsers...")
        os.system("playwright install chromium")

    asyncio.run(main())
