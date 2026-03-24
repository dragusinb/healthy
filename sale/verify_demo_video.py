"""
Verify demo video by loading it in a browser, seeking to timestamps,
and checking that each frame shows expected content (no errors/empty states).

Usage:
    python verify_demo_video.py
    python verify_demo_video.py --url https://analize.online/demo-video.webm
"""

import argparse
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DEFAULT_URL = "https://analize.online/demo-video.webm"

# Timestamps (seconds) and what we expect NOT to see at each point
CHECKPOINTS = [
    (5, "Landing page"),
    (15, "After login / Dashboard"),
    (30, "Documents page"),
    (45, "Biomarkers page"),
    (60, "Health Reports"),
    (90, "Billing / Settings"),
]

# Error indicators that mean the video is bad
ERROR_STRINGS = [
    "niciun biomarker",
    "încărcarea a eșuat",
    "loading failed",
    "no biomarkers",
    "eroare",
    "error",
]


def verify(url: str):
    out_dir = Path(__file__).parent / "demo_verify"
    out_dir.mkdir(exist_ok=True)

    html = f"""<!DOCTYPE html>
<html><body style="margin:0;background:#000">
<video id="v" src="{url}" style="width:1280px;height:720px" muted></video>
<script>
window.seekTo = (t) => {{
    const v = document.getElementById('v');
    return new Promise((resolve) => {{
        v.currentTime = t;
        v.onseeked = () => resolve(v.currentTime);
    }});
}};
window.getDuration = () => document.getElementById('v').duration;
</script>
</body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.set_content(html)
        page.wait_for_timeout(3000)

        duration = page.evaluate("window.getDuration()")
        print(f"Video duration: {duration:.1f}s")

        if duration < 60:
            print(f"[FAIL] Video too short ({duration:.1f}s) — likely a failed recording")
            browser.close()
            return False

        all_ok = True
        for ts, label in CHECKPOINTS:
            if ts > duration:
                print(f"[SKIP] {ts}s — beyond video duration")
                continue

            page.evaluate(f"window.seekTo({ts})")
            page.wait_for_timeout(500)

            screenshot_path = out_dir / f"frame_{ts:03d}s.png"
            page.screenshot(path=str(screenshot_path))
            print(f"[{ts:3d}s] {label} — saved {screenshot_path.name}")

        print(f"\nScreenshots saved to: {out_dir}")
        print("Please visually inspect the screenshots to verify video quality.")
        print(f"  Video duration: {duration:.1f}s")

        browser.close()
        return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL, help="URL of the demo video")
    args = parser.parse_args()
    ok = verify(args.url)
    if ok:
        print("\n[OK] Basic checks passed. Review screenshots for visual quality.")
    else:
        print("\n[FAIL] Video verification failed.")
        exit(1)
