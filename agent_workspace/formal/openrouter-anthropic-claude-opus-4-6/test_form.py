"""
End-to-end Playwright test for the 3-step registration form (form.html).
Uses sync API, data-testid selectors, and retry logic for resilience.
"""

import time
import pathlib
from playwright.sync_api import sync_playwright, expect, TimeoutError as PwTimeout

# ── Test data ──────────────────────────────────────────────────────────────────
PERSONAL = {
    "fullname": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+1 555-987-6543",
}

ADDRESS = {
    "street": "742 Evergreen Terrace",
    "city": "Springfield",
    "state": "CA",            # value attribute in the <select>
    "state_label": "California",  # display text for review verification
    "zip": "90210",
}

FORM_PATH = pathlib.Path(__file__).resolve().parent / "form.html"
SCREENSHOT_PATH = pathlib.Path(__file__).resolve().parent / "success.png"


# ── Retry helper ───────────────────────────────────────────────────────────────
def retry(action, *, retries=3, delay=0.5):
    """Run *action* (a callable) up to *retries* times, sleeping between attempts."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return action()
        except (PwTimeout, Exception) as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


# ── Selector helpers ───────────────────────────────────────────────────────────
def tid(name: str) -> str:
    """Return a data-testid selector string."""
    return f"[data-testid=\"{name}\"]"


def fill_field(page, testid: str, value: str):
    """Fill an input identified by data-testid, with retry."""
    retry(lambda: page.locator(tid(testid)).fill(value))


def click_button(page, testid: str):
    """Click a button identified by data-testid, with retry."""
    retry(lambda: page.locator(tid(testid)).click())


# ── Step assertions ────────────────────────────────────────────────────────────
def assert_step_visible(page, step_num: int):
    """Assert that exactly the given step panel is visible and others are not."""
    for i in range(1, 4):
        loc = page.locator(tid(f"step-{i}"))
        if i == step_num:
            retry(lambda loc=loc: expect(loc).to_be_visible())
        else:
            retry(lambda loc=loc: expect(loc).to_be_hidden())


def assert_progress_bar(page, active_up_to: int):
    """Assert progress-bar segments: active for steps ≤ active_up_to."""
    for i in range(1, 4):
        seg = page.locator(f"#prog-{i}")
        if i <= active_up_to:
            retry(lambda seg=seg: expect(seg).to_have_class("progress-step active"))
        else:
            retry(lambda seg=seg: expect(seg).to_have_class("progress-step"))


# ── Main test ──────────────────────────────────────────────────────────────────
def test_registration_form():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FORM_PATH.as_uri())

        # ── Step 1: Personal Info ─────────────────────────────────────────
        assert_step_visible(page, 1)
        assert_progress_bar(page, 1)

        fill_field(page, "fullname", PERSONAL["fullname"])
        fill_field(page, "email", PERSONAL["email"])
        fill_field(page, "phone", PERSONAL["phone"])
        click_button(page, "next-1")

        # ── Step 2: Address ───────────────────────────────────────────────
        assert_step_visible(page, 2)
        assert_progress_bar(page, 2)

        fill_field(page, "street", ADDRESS["street"])
        fill_field(page, "city", ADDRESS["city"])
        retry(lambda: page.locator(tid("state")).select_option(ADDRESS["state"]))
        fill_field(page, "zip", ADDRESS["zip"])
        click_button(page, "next-2")

        # ── Step 3: Review ────────────────────────────────────────────────
        assert_step_visible(page, 3)
        assert_progress_bar(page, 3)

        # Verify review values match what we entered
        retry(lambda: expect(page.locator(tid("review-fullname"))).to_have_text(PERSONAL["fullname"]))
        retry(lambda: expect(page.locator(tid("review-email"))).to_have_text(PERSONAL["email"]))
        retry(lambda: expect(page.locator(tid("review-phone"))).to_have_text(PERSONAL["phone"]))

        expected_address = (
            f"{ADDRESS['street']}, {ADDRESS['city']}, "
            f"{ADDRESS['state']} {ADDRESS['zip']}"
        )
        retry(lambda: expect(page.locator(tid("review-address"))).to_have_text(expected_address))

        # Submit
        click_button(page, "submit")

        # ── Success panel ─────────────────────────────────────────────────
        success = page.locator(tid("success-panel"))
        retry(lambda: expect(success).to_be_visible())

        # Step 3 should be gone, success panel shown
        retry(lambda: expect(page.locator(tid("step-3"))).to_be_hidden())

        # Submission ID present and non-empty (format: REG-XXXXXXXX)
        sub_id_loc = page.locator(tid("submission-id"))
        retry(lambda: expect(sub_id_loc).to_be_visible())
        sub_id = sub_id_loc.text_content()
        assert sub_id and sub_id.startswith("REG-"), f"Unexpected submission ID: {sub_id}"

        # Screenshot the success state
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)

        browser.close()

    print(f"✅ All checks passed. Submission ID: {sub_id}")
    print(f"📸 Screenshot saved to {SCREENSHOT_PATH}")


if __name__ == "__main__":
    test_registration_form()
