from pathlib import Path
import re
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


FULL_NAME = "Jordan Lee"
EMAIL = "jordan.lee@example.com"
PHONE = "+1 555-123-4567"
STREET = "123 Main St"
CITY = "San Francisco"
STATE_VALUE = "CA"
STATE_LABEL = "California"
ZIP_CODE = "94102"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.4


def retry_action(action, description, retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                raise AssertionError(
                    f"Failed to {description} after {retries} attempts"
                ) from exc
            time.sleep(delay)
    raise last_error


def testid(page, value):
    return page.get_by_test_id(value)


def active_progress_count(page):
    return page.locator(".progress-step.active").count()


def assert_step_state(page, step_number):
    for i in range(1, 4):
        step = testid(page, f"step-{i}")
        if i == step_number:
            expect(step).to_be_visible()
            expect(step).to_have_class(re.compile(r"\bstep active\b|\bactive step\b|\bstep\b.*\bactive\b"))
        else:
            expect(step).not_to_be_visible()

    expect(testid(page, "progress-bar")).to_be_visible()
    assert active_progress_count(page) == step_number, (
        f"Expected {step_number} active progress steps, got {active_progress_count(page)}"
    )

    for i in range(1, 4):
        progress = page.locator(f"#prog-{i}")
        cls = retry_action(lambda: progress.get_attribute("class"), f"read progress class for step {i}") or ""
        if i <= step_number:
            assert "active" in cls, f"Progress step {i} should be active, got: {cls}"
        else:
            assert "active" not in cls, f"Progress step {i} should be inactive, got: {cls}"


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    form_path = Path(__file__).with_name("form.html").resolve()
    page.goto(form_path.as_uri())

    expect(testid(page, "form-container")).to_be_visible()
    assert_step_state(page, 1)

    retry_action(lambda: testid(page, "fullname").fill(FULL_NAME), "fill full name")
    retry_action(lambda: testid(page, "email").fill(EMAIL), "fill email")
    retry_action(lambda: testid(page, "phone").fill(PHONE), "fill phone")
    retry_action(lambda: testid(page, "next-1").click(), "click next on step 1")

    assert_step_state(page, 2)

    retry_action(lambda: testid(page, "street").fill(STREET), "fill street")
    retry_action(lambda: testid(page, "city").fill(CITY), "fill city")
    retry_action(lambda: testid(page, "state").select_option(STATE_VALUE), "select state")
    retry_action(lambda: testid(page, "zip").fill(ZIP_CODE), "fill ZIP code")
    retry_action(lambda: testid(page, "next-2").click(), "click next on step 2")

    assert_step_state(page, 3)

    expect(testid(page, "review-fullname")).to_have_text(FULL_NAME)
    expect(testid(page, "review-email")).to_have_text(EMAIL)
    expect(testid(page, "review-phone")).to_have_text(PHONE)
    expect(testid(page, "review-address")).to_have_text(
        f"{STREET}, {CITY}, {STATE_VALUE} {ZIP_CODE}"
    )

    retry_action(lambda: testid(page, "submit").click(), "submit the form")

    success_panel = testid(page, "success-panel")
    expect(success_panel).to_be_visible()

    submission_id = testid(page, "submission-id")
    expect(submission_id).to_be_visible()
    submission_text = retry_action(
        lambda: submission_id.text_content(), "read submission ID text"
    )
    assert submission_text, "Submission ID should not be empty"
    assert re.fullmatch(r"REG-[A-Z0-9]{8}", submission_text.strip()), (
        f"Unexpected submission ID format: {submission_text!r}"
    )

    success_path = Path(__file__).with_name("success.png")
    page.screenshot(path=str(success_path), full_page=True)

    browser.close()
