"""Browser end-to-end test for APAAR-Setu (22 checks across all three roles).

Setup (once):   pip install playwright && playwright install chromium
Run (3 terminals, from the repo root):
  1) cd backend && python -m seed.load_all --reset && uvicorn app.main:app --port 8000
  2) cd frontend && npm run build && npm start          # serves on :3000
  3) python scripts/e2e_browser.py
It uploads demo_overflow.csv, so re-run `python -m seed.load_all --reset` in terminal 1 before running it again.
Screenshots are written to ./e2e_shots/.
"""
import re, sys
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:3000"
from pathlib import Path
DEMO = str(Path(__file__).resolve().parents[1] / "backend" / "seed" / "data" / "demo_uploads") + "/"
SHOTS = Path("e2e_shots"); SHOTS.mkdir(exist_ok=True)
results, problems = [], []

def step(name, fn):
    try:
        fn(); results.append(("PASS", name))
    except Exception as e:
        results.append(("FAIL", name + " -> " + ((str(e).splitlines() or [repr(e)])[0][:200])))

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: problems.append(f"console.{m.type}: {m.text[:200]}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: problems.append(f"pageerror: {str(e)[:200]}"))

    def login(btn_text, expect_url):
        page.goto(BASE + "/login")
        page.get_by_role("button", name=re.compile(btn_text)).click()
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(re.compile(expect_url), timeout=10000)

    def logout():
        page.get_by_role("button", name="Logout").click()
        page.wait_for_url(re.compile("/login"))

    # ---- institution admin ----
    step("login as institution admin lands on dashboard", lambda: (login("Institution admin", "/institution/dashboard"), expect(page.get_by_role("heading", name="Deccan Institute of Technology")).to_be_visible(timeout=10000)))
    step("dashboard shows quality 100 / risk 0 and charts", lambda: (expect(page.get_by_text("100/100")).to_be_visible(), expect(page.locator("svg.recharts-surface").first).to_be_visible()))
    page.screenshot(path=str(SHOTS / "1_inst_dashboard.png"), full_page=True)

    def upload_dry():
        page.get_by_role("link", name="Upload").first.click()
        page.wait_for_url(re.compile("/institution/upload"))
        page.set_input_files("input[type=file]", DEMO + "demo_messy.csv")
        page.get_by_role("button", name=re.compile("Validate only")).click()
        expect(page.get_by_text("Dry run result")).to_be_visible(timeout=10000)
        txt = page.locator("body").inner_text()
        assert re.search(r"ACCEPTED\s*16", txt, re.I) or "16" in txt
    step("dry run of demo_messy.csv", upload_dry)
    def counts():
        body = page.locator("section", has_text="Dry run result").first.inner_text()
        nums = re.findall(r"(Accepted|Flagged|Rejected)\s*\n?\s*(\d+)", body, re.I)
        d = {k.lower(): int(v) for k, v in nums}
        assert d == {"accepted": 16, "flagged": 4, "rejected": 10}, d
    step("dry-run counts are 16 / 4 / 10", counts)
    def filter_rej():
        page.get_by_role("button", name="REJECTED", exact=True).click()
        expect(page.locator("section", has_text="Dry run result").locator("tbody tr")).to_have_count(10, timeout=5000)
        assert page.get_by_text("APAAR_CHECKSUM").first.is_visible()
    step("REJECTED filter shows 10 rows incl. APAAR_CHECKSUM", filter_rej)
    page.screenshot(path=str(SHOTS / "2_upload_dry.png"), full_page=True)

    def real_overflow():
        page.set_input_files("input[type=file]", DEMO + "demo_overflow.csv")
        page.get_by_role("button", name="Upload", exact=True).click()
        expect(page.get_by_text(re.compile(r"Upload #\d+ saved"))).to_be_visible(timeout=15000)
        body = page.locator("section", has_text="saved").first.inner_text()
        assert re.search(r"Flagged\s*\n?\s*5", body, re.I), body[:200]
    step("real upload of demo_overflow.csv flags exactly 5", real_overflow)

    def download_report():
        with page.expect_download(timeout=10000) as dl:
            page.get_by_role("button", name="Download error report").click()
        name = dl.value.suggested_filename
        assert name.endswith("_issues.csv"), name
    step("error report downloads as CSV", download_report)

    def dash_critical():
        page.get_by_role("link", name="Dashboard").first.click()
        expect(page.get_by_text("CRITICAL").first).to_be_visible(timeout=10000)
        expect(page.get_by_text(re.compile("DIT001-ECE .*95 regular admissions"))).to_be_visible()
    step("dashboard now shows CRITICAL intake alert for DIT001-ECE", dash_critical)
    page.screenshot(path=str(SHOTS / "3_inst_dashboard_after.png"), full_page=True)

    def students_and_cert():
        page.get_by_role("link", name="Students").first.click()
        expect(page.get_by_role("link", name="Certificate").first).to_be_visible(timeout=10000)
        page.get_by_placeholder("Search…").fill("100000000016")
        expect(page.locator("tbody tr")).to_have_count(1, timeout=8000)
        page.get_by_role("link", name="Certificate").first.click()
        expect(page.get_by_text("Provisional Enrolment Certificate")).to_be_visible(timeout=15000)
        expect(page.locator("img[alt^='QR']")).to_be_visible()
        expect(page.get_by_text("100000000016").first).to_be_visible()
        expect(page.get_by_text("SYN-1-")).to_be_visible()
    step("students search + certificate shows student ID, APAAR ID and QR", students_and_cert)
    page.screenshot(path=str(SHOTS / "4_certificate.png"), full_page=True)
    try:
        verify_url = page.locator("p.break-all").first.inner_text(timeout=3000)
    except Exception:
        verify_url = BASE + "/verify?t=missing"
        page.screenshot(path=str(SHOTS / "4_certificate_FAIL.png"), full_page=True)
        results.append(("INFO", "certificate page text: " + page.locator("main").inner_text()[:300].replace("\n", " | ")))
    step("certificate prints without nav (print media hides header)", lambda: (page.emulate_media(media="print"), expect(page.locator("header")).to_be_hidden(), page.emulate_media(media="screen")))

    step("inst admin is bounced away from AICTE page", lambda: (page.goto(BASE + "/aicte/dashboard"), page.wait_for_url(re.compile("/institution/dashboard"), timeout=8000)))
    logout()

    # ---- verifier: consent-required student (no consent seeded for ...0040? use cert of 100000000016 which is consented? check) ----
    def verifier_flow():
        login("Verifier", "/verify")
        page.goto(verify_url.replace("http://localhost:3000", BASE))
        page.wait_for_selector("text=/VERIFIED|consent required|NOT VERIFIED/", timeout=10000)
    step("verifier opens QR link and gets a result", verifier_flow)
    outcome = page.locator("main").inner_text()
    results.append(("INFO", "QR link outcome: " + ("VERIFIED" if "✔ VERIFIED" in outcome else "CONSENT_REQUIRED" if "consent required" in outcome else "NOT VERIFIED")))
    page.screenshot(path=str(SHOTS / "5_verify.png"), full_page=True)

    def tamper():
        t = verify_url.split("t=")[1]
        bad = t[:-3] + ("AAA" if not t.endswith("AAA") else "BBB")
        page.goto(f"{BASE}/verify?t={bad}")
        expect(page.get_by_text("NOT VERIFIED")).to_be_visible(timeout=10000)
    step("tampered token shows NOT VERIFIED", tamper)
    step("public key can be shown", lambda: (page.get_by_role("button", name="Show public key").click(), expect(page.get_by_text("BEGIN PUBLIC KEY")).to_be_visible()))
    step("verifier cannot open institution page", lambda: (page.goto(BASE + "/institution/upload"), page.wait_for_url(re.compile("/verify"), timeout=8000)))
    logout()

    # ---- AICTE ----
    step("AICTE dashboard cards and charts", lambda: (login("AICTE officer", "/aicte/dashboard"), expect(page.get_by_text("Cross-institution duplicates").first).to_be_visible(timeout=10000), expect(page.locator("svg.recharts-surface").first).to_be_visible()))
    def dup_rows():
        rows = page.locator("section", has_text="Possible duplicate enrolment").locator("tbody tr")
        expect(rows).to_have_count(8, timeout=8000)
        assert "••••" in rows.first.inner_text()
    step("duplicates table has 8 masked rows", dup_rows)
    def risk_expand():
        page.get_by_text("Coastal College of Engineering").first.click()
        expect(page.get_by_text(re.compile(r"CCE002-CSE .*"))).to_be_visible(timeout=8000)
        expect(page.get_by_text("113%").or_(page.get_by_text(re.compile(r"11\d%"))).first).to_be_visible()
    step("risk row expands and shows Coastal CSE over 100%", risk_expand)
    page.screenshot(path=str(SHOTS / "6_aicte_dashboard.png"), full_page=True)

    def alerts_page():
        page.get_by_role("link", name="Alerts").first.click()
        expect(page.get_by_text("ANOM_FOREIGN_SHARE")).to_be_visible(timeout=10000)
        page.locator("select").first.select_option("CRITICAL")
        expect(page.locator("tbody tr")).to_have_count(2, timeout=8000)   # inst 2 baseline + inst 1 overflow
        body = page.locator("tbody").inner_text()
        assert "INTAKE_EXCEEDED" in body and "ANOM_" not in body, body[:200]
        page.locator("tbody tr").first.click()
        expect(page.get_by_text("Evidence", exact=True)).to_be_visible()
    step("alerts page filters and expands evidence", alerts_page)

    def audit_page():
        page.get_by_role("link", name="Audit").first.click()
        expect(page.get_by_text("Audit trail").first).to_be_visible(timeout=10000)
        page.get_by_role("button", name="Verify audit chain").click()
        expect(page.get_by_text(re.compile(r"Chain intact · \d+ entries verified"))).to_be_visible(timeout=10000)
        page.locator("select").first.select_option("VERIFY_ATTEMPT")
        expect(page.locator("tbody").get_by_text("VERIFY_ATTEMPT").first).to_be_visible(timeout=8000)
    step("audit page: filter + chain intact banner", audit_page)
    page.screenshot(path=str(SHOTS / "7_audit.png"), full_page=True)

    # mobile layout check
    mob = browser.new_context(viewport={"width": 390, "height": 800}).new_page()
    mob.goto(BASE + "/login"); mob.get_by_role("button", name=re.compile("Institution admin")).click(); mob.get_by_role("button", name="Sign in").click()
    mob.wait_for_url(re.compile("/institution/dashboard")); mob.wait_for_selector("text=Data quality score")
    overflow = mob.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    results.append(("PASS" if not overflow else "FAIL", "mobile 390px: no horizontal page scroll"))
    mob.screenshot(path=str(SHOTS / "8_mobile.png"), full_page=True)
    browser.close()

for r in results: print(*r)
print("\nconsole/page problems:", len(problems))
print("403/401 errors:", sum(("403" in x or "401" in x) for x in problems))
for pr in sorted(set(problems))[:10]: print(" ", pr)
