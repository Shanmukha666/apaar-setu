"""Automated demo walkthrough and video recorder for APAAR-Setu.

Records a complete end-to-end video of the working prototype using Playwright
with realistic pacing, smooth scrolling, and complete coverage of all SIH26263 features.
"""
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_FILES = ROOT / "backend" / "seed" / "data" / "demo_uploads"
VIDEO_DIR = ROOT / "demo_video"
SHOTS_DIR = ROOT / "demo_video" / "screenshots"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"


def wait_for_url(url: str, timeout: int = 35):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status in (200, 304, 307):
                    return True
        except Exception:
            time.sleep(0.8)
    return False


def run_recording():
    from playwright.sync_api import sync_playwright

    print("[1/5] Resetting baseline synthetic database...", flush=True)
    backend_dir = ROOT / "backend"
    subprocess.run([sys.executable, "-m", "seed.load_all", "--reset"], cwd=str(backend_dir), check=True)

    print("[2/5] Launching backend server on port 8000...", flush=True)
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(backend_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[3/5] Launching frontend server on port 3000...", flush=True)
    frontend_dir = ROOT / "frontend"
    frontend_proc = subprocess.Popen(
        ["npx.cmd", "next", "start", "-p", "3000"],
        cwd=str(frontend_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        print("[4/5] Waiting for servers to be healthy...", flush=True)
        if not wait_for_url(f"{API_URL}/api/health", 30):
            raise RuntimeError("Backend failed to start on port 8000")
        if not wait_for_url(BASE_URL, 30):
            raise RuntimeError("Frontend failed to start on port 3000")
        print("Both servers healthy! Starting Playwright browser recording...", flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(VIDEO_DIR),
                record_video_size={"width": 1280, "height": 720},
            )
            page = context.new_page()

            def pace(seconds: float = 1.8):
                page.wait_for_timeout(int(seconds * 1000))

            def smooth_scroll(y: int = 400):
                page.evaluate(f"window.scrollBy({{ top: {y}, behavior: 'smooth' }});")
                pace(1.0)

            # ----------------------------------------------------
            # SCENE 1: Portal Login & Governance Portal Header
            # ----------------------------------------------------
            print("Scene 1: Login & Governance Portal Header...", flush=True)
            page.goto(f"{BASE_URL}/login")
            pace(2.2)
            page.screenshot(path=str(SHOTS_DIR / "01_login.png"))

            # Click AICTE preset
            page.get_by_text("AICTE Regulatory Officer").first.click()
            pace(1.0)
            page.get_by_role("button", name="Access Portal").click()
            page.wait_for_url("**/aicte/dashboard", timeout=15000)
            pace(2.5)

            # ----------------------------------------------------
            # SCENE 2: AICTE National Regulatory Dashboard
            # ----------------------------------------------------
            print("Scene 2: AICTE National Dashboard & Risk Heuristics...", flush=True)
            page.screenshot(path=str(SHOTS_DIR / "02_aicte_dashboard.png"))
            pace(2.0)

            # Scroll down to charts & duplicate detection
            smooth_scroll(380)
            page.screenshot(path=str(SHOTS_DIR / "03_national_charts.png"))
            pace(2.0)

            smooth_scroll(450)
            page.screenshot(path=str(SHOTS_DIR / "04_cross_duplicates.png"))
            pace(2.0)

            # Open Risk Explainer dialog
            risk_btn = page.locator("button:has-text('ℹ')").first
            if risk_btn.is_visible():
                risk_btn.click()
                pace(2.5)
                page.screenshot(path=str(SHOTS_DIR / "05_risk_modal.png"))
                close_btn = page.locator("button:has-text('✕')").first
                if close_btn.is_visible():
                    close_btn.click()
                pace(1.2)

            # Scroll back to top
            page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            pace(1.2)

            # ----------------------------------------------------
            # SCENE 3: Cryptographic Audit Trail (Hash Chain)
            # ----------------------------------------------------
            print("Scene 3: Cryptographic Audit Trail & Tamper Detection...", flush=True)
            page.get_by_role("link", name="Audit Trail").click()
            page.wait_for_url("**/aicte/audit", timeout=10000)
            pace(2.0)
            page.screenshot(path=str(SHOTS_DIR / "06_audit_trail.png"))

            # Verify intact chain
            page.get_by_role("button", name="Verify audit chain").click()
            pace(2.2)
            page.screenshot(path=str(SHOTS_DIR / "07_audit_verified.png"))

            # Simulate tampering
            page.get_by_role("button", name="⚡ Simulate DB Tamper").click()
            pace(2.5)
            page.screenshot(path=str(SHOTS_DIR / "08_audit_tampered.png"))

            # Restore integrity
            page.get_by_role("button", name="↺ Restore Chain").click()
            pace(2.2)
            page.screenshot(path=str(SHOTS_DIR / "09_audit_restored.png"))

            # ----------------------------------------------------
            # SCENE 4: Statutory Reports Export
            # ----------------------------------------------------
            print("Scene 4: Statutory Enrolment Reports...", flush=True)
            page.get_by_role("link", name="Regulatory Reports").click()
            page.wait_for_url("**/aicte/reports", timeout=10000)
            pace(2.2)
            page.screenshot(path=str(SHOTS_DIR / "10_reports.png"))

            # Sign Out
            page.get_by_role("button", name="Sign Out").click()
            page.wait_for_url("**/login", timeout=10000)
            pace(1.5)

            # ----------------------------------------------------
            # SCENE 5: Institution Admin Dashboard
            # ----------------------------------------------------
            print("Scene 5: Institution Admin (Deccan Institute of Tech)...", flush=True)
            page.get_by_text("Institution Admin").first.click()
            pace(0.8)
            page.get_by_role("button", name="Access Portal").click()
            page.wait_for_url("**/institution/dashboard", timeout=15000)
            pace(2.5)
            page.screenshot(path=str(SHOTS_DIR / "11_institution_dashboard.png"))
            smooth_scroll(350)
            pace(1.8)
            page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            pace(1.0)

            # ----------------------------------------------------
            # SCENE 6: Student Registry & DPDP Consent Simulation
            # ----------------------------------------------------
            print("Scene 6: Student Registry & DPDP Consent Management...", flush=True)
            page.get_by_role("link", name="Student Registry").click()
            page.wait_for_url("**/institution/students", timeout=10000)
            pace(2.0)
            page.screenshot(path=str(SHOTS_DIR / "12_students_registry.png"))

            # Open Consent dialog for a student
            consent_btn = page.locator("button:has-text('Consent')").first
            if consent_btn.is_visible():
                consent_btn.click()
                pace(2.2)
                page.screenshot(path=str(SHOTS_DIR / "13_dpdp_consent_dialog.png"))
                # Toggle Consent
                toggle_btn = page.locator("button:has-text('Revoke Consent'), button:has-text('Grant Consent')").first
                if toggle_btn.is_visible():
                    toggle_btn.click()
                    pace(2.0)
                    page.screenshot(path=str(SHOTS_DIR / "14_consent_updated.png"))
                close_consent = page.locator("button:has-text('Close')").first
                if close_consent.is_visible():
                    close_consent.click()
                pace(1.2)

            # ----------------------------------------------------
            # SCENE 7: Multi/Bulk CSV Upload & Validation Engine
            # ----------------------------------------------------
            print("Scene 7: Multi/Bulk CSV Upload & Validation Engine...", flush=True)
            page.get_by_role("link", name="Ingest & Validate").click()
            page.wait_for_url("**/institution/upload", timeout=10000)
            pace(1.8)
            page.screenshot(path=str(SHOTS_DIR / "15_upload_page.png"))

            # Test Dry-Run with demo_messy.csv
            messy_path = str(DEMO_FILES / "demo_messy.csv")
            page.set_input_files("input[type=file]", messy_path)
            pace(1.5)
            page.get_by_role("button", name="Validate only (dry run)").click()
            pace(3.0)
            page.screenshot(path=str(SHOTS_DIR / "16_dry_run_results.png"))

            # Filter rejected
            page.get_by_role("button", name="REJECTED").click()
            pace(2.0)
            page.screenshot(path=str(SHOTS_DIR / "17_rejected_issues.png"))

            # Filter flagged
            page.get_by_role("button", name="FLAGGED").click()
            pace(2.0)

            # Real Upload with demo_clean.csv
            clean_path = str(DEMO_FILES / "demo_clean.csv")
            page.set_input_files("input[type=file]", clean_path)
            pace(1.2)
            page.get_by_role("button", name="Upload").click()
            pace(3.0)
            page.screenshot(path=str(SHOTS_DIR / "18_upload_clean_saved.png"))

            # ----------------------------------------------------
            # SCENE 8: Verifiable Academic Certificate
            # ----------------------------------------------------
            print("Scene 8: Verifiable Digital Academic Certificate with QR...", flush=True)
            page.goto(f"{BASE_URL}/certificate/100000007227?year=2026-27")
            pace(3.0)
            page.screenshot(path=str(SHOTS_DIR / "19_academic_certificate.png"))
            smooth_scroll(300)
            pace(1.8)

            verify_url = ""
            try:
                verify_url = page.locator("article p.break-all").inner_text(timeout=4000)
            except Exception:
                pass

            # ----------------------------------------------------
            # SCENE 9: Public Verifier Portal & Verification
            # ----------------------------------------------------
            print("Scene 9: Public Autonomous Verification...", flush=True)
            if verify_url and "verify?t=" in verify_url:
                page.goto(verify_url)
            else:
                page.goto(f"{BASE_URL}/verify")
            pace(2.5)
            page.screenshot(path=str(SHOTS_DIR / "20_verify_portal.png"))

            # Show public key
            pubkey_btn = page.get_by_role("button", name="Show statutory root public key")
            if pubkey_btn.is_visible():
                pubkey_btn.click()
                pace(2.0)
                page.screenshot(path=str(SHOTS_DIR / "21_public_key.png"))

            smooth_scroll(250)
            pace(2.0)

            # ----------------------------------------------------
            # SCENE 10: Conclusion
            # ----------------------------------------------------
            print("Scene 10: Returning to home...", flush=True)
            page.goto(f"{BASE_URL}/login")
            pace(2.5)

            # Finalize video
            context.close()
            browser.close()

        print("[5/5] Processing recorded video...", flush=True)
        recorded_files = [f for f in VIDEO_DIR.glob("*.webm") if f.name != "apaar_setu_prototype_demo.webm"]
        if recorded_files:
            latest_video = max(recorded_files, key=lambda f: f.stat().st_mtime)
            final_target = VIDEO_DIR / "apaar_setu_prototype_demo.webm"
            shutil.copy2(latest_video, final_target)
            print(f"Video recorded successfully: {final_target} ({final_target.stat().st_size // 1024} KB)", flush=True)
        else:
            print("Warning: No video file found in output directory", flush=True)

    finally:
        print("Cleaning up background servers...", flush=True)
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()
        try:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()


if __name__ == "__main__":
    run_recording()
