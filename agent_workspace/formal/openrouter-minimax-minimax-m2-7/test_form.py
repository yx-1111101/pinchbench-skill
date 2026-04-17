"""
Playwright end-to-end test for form.html — 3-step registration form.
"""

import re
import time
from playwright.sync_api import Page, sync_playwright

# ── Retry helper ──────────────────────────────────────────────────────────────

def retry_click(page: Page, testid: str, retries: int = 3, delay: float = 0.5):
    """Click the element matching [data-testid=<testid>], retrying on failure."""
    selector = f"[data-testid='{testid}']"
    for attempt in range(1, retries + 1):
        try:
            page.wait_for_selector(selector, state="visible", timeout=3000)
            page.click(selector)
            return
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(
                    f"Failed to click data-testid='{testid}' after {retries} attempts"
                ) from e
            time.sleep(delay)


def retry_fill(page: Page, testid: str, value: str, retries: int = 3, delay: float = 0.5):
    """Fill the input matching [data-testid=<testid>], retrying on failure."""
    selector = f"[data-testid='{testid}']"
    for attempt in range(1, retries + 1):
        try:
            page.wait_for_selector(selector, state="visible", timeout=3000)
            page.fill(selector, value)
            return
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(
                    f"Failed to fill data-testid='{testid}' after {retries} attempts"
                ) from e
            time.sleep(delay)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def assert_visible(page: Page, testid: str):
    """Assert that an element with the given data-testid is visible."""
    selector = f"[data-testid='{testid}']"
    if not page.is_visible(selector):
        raise AssertionError(f"Expected [data-testid='{testid}'] to be visible")


def assert_hidden(page: Page, testid: str):
    """Assert that an element with the given data-testid is hidden."""
    selector = f"[data-testid='{testid}']"
    if page.is_visible(selector):
        raise AssertionError(f"Expected [data-testid='{testid}'] to be hidden")


def assert_step_active(page: Page, step_number: int):
    """Assert that the given step is active and all other steps are hidden."""
    for i in range(1, 4):
        testid = f"step-{i}"
        if i == step_number:
            assert_visible(page, testid)
        else:
            assert_hidden(page, testid)


def assert_progress_bar(page: Page, active_steps: int):
    """
    Assert that exactly the first `active_steps` progress indicators are active.
    progress-step active = blue, inactive = grey (#e0e0e0).
    """
    for i in range(1, 4):
        prog_id = f"prog-{i}"
        is_active = page.evaluate(
            f"document.getElementById('{prog_id}').classList.contains('active')"
        )
        expected = i <= active_steps
        if is_active != expected:
            raise AssertionError(
                f"Progress step {i}: expected active={expected}, got active={is_active}"
            )


def assert_text(page: Page, testid: str, pattern: str | re.Pattern):
    """Assert that the element's text content matches (or contains) the pattern."""
    selector = f"[data-testid='{testid}']"
    text = page.text_content(selector)
    if isinstance(pattern, re.Pattern):
        if not pattern.search(text):
            raise AssertionError(
                f"[data-testid='{testid}'] text '{text}' does not match {pattern}"
            )
    else:
        if pattern not in text:
            raise AssertionError(
                f"[data-testid='{testid}'] text '{text}' does not contain '{pattern}'"
            )


# ── Test ─────────────────────────────────────────────────────────────────────

def run():
    form_url = "file:///root/.openclaw/workspace/pinchbench-skill/agent_workspace/formal/openrouter-minimax-minimax-m2-7/form.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── STEP 0: Load ────────────────────────────────────────────────────
        page.goto(form_url)
        assert_visible(page, "form-container")
        assert_visible(page, "step-1")
        assert_hidden(page, "step-2")
        assert_hidden(page, "step-3")
        assert_hidden(page, "success-panel")
        assert_progress_bar(page, active_steps=1)
        print("✓ Form loaded; Step 1 visible, progress bar at step 1/3")

        # ── STEP 1: Personal Info ─────────────────────────────────────────────
        retry_fill(page, "fullname", "Jane Doe")
        retry_fill(page, "email", "jane.doe@example.com")
        retry_fill(page, "phone", "+1 555-987-6543")
        retry_click(page, "next-1")
        page.wait_for_timeout(400)  # allow transition animation

        assert_step_active(page, 2)
        assert_hidden(page, "step-1")
        assert_hidden(page, "step-3")
        assert_progress_bar(page, active_steps=2)
        print("✓ Step 1 filled and validated; Step 2 visible, progress bar at step 2/3")

        # ── STEP 2: Address ──────────────────────────────────────────────────
        retry_fill(page, "street", "742 Evergreen Terrace")
        retry_fill(page, "city", "Springfield")
        retry_click(page, "state")           # open the dropdown
        page.select_option("[data-testid='state']", "CA")
        retry_fill(page, "zip", "94102")     # 5-digit ZIP — passes validation

        retry_click(page, "next-2")
        page.wait_for_timeout(400)

        assert_step_active(page, 3)
        assert_hidden(page, "step-1")
        assert_hidden(page, "step-2")
        assert_progress_bar(page, active_steps=3)
        print("✓ Step 2 filled and validated; Step 3 visible, progress bar at step 3/3")

        # ── STEP 3: Review ──────────────────────────────────────────────────
        assert_text(page, "review-fullname", "Jane Doe")
        assert_text(page, "review-email", "jane.doe@example.com")
        assert_text(page, "review-phone", "+1 555-987-6543")
        assert_text(page, "review-address", re.compile(r"742 Evergreen Terrace"))
        assert_text(page, "review-address", re.compile(r"Springfield"))
        assert_text(page, "review-address", re.compile(r", CA "))
        assert_text(page, "review-address", re.compile(r"94102"))
        print("✓ Review summary shows all correct data")

        retry_click(page, "submit")
        page.wait_for_timeout(400)

        # ── SUCCESS ─────────────────────────────────────────────────────────
        assert_hidden(page, "step-3")
        assert_visible(page, "success-panel")
        submission_id = page.text_content("[data-testid='submission-id']")
        if not submission_id or not submission_id.startswith("REG-"):
            raise AssertionError(
                f"Submission ID '{submission_id}' does not match expected format REG-XXXXXXXX"
            )
        print(f"✓ Success panel visible; submission ID = {submission_id}")

        page.screenshot(path="success.png", full_page=True)
        print("✓ Screenshot saved as success.png")

        browser.close()
        print("\n✅ All checks passed — form works end-to-end.")


if __name__ == "__main__":
    run()
