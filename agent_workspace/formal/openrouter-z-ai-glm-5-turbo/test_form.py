import re
from pathlib import Path
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


RETRIES = 3
RETRY_DELAY_SECONDS = 0.4

TEST_DATA = {
    "full_name": "Jordan Lee",
    "email": "jordan.lee@example.com",
    "phone": "+1 555-123-4567",
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "state_label": "California",
    "zip": "94102",
}


def retry_action(action, description):
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == RETRIES:
                raise AssertionError(
                    f"Failed to {description} after {RETRIES} attempts"
                ) from exc
            sleep(RETRY_DELAY_SECONDS)
    raise last_error


def retry_fill(locator, value, description):
    def action():
        locator.wait_for(state="visible", timeout=3000)
        locator.fill(value)
        expect(locator).to_have_value(value)

    retry_action(action, description)


def retry_click(locator, description):
    def action():
        locator.wait_for(state="visible", timeout=3000)
        locator.click()

    retry_action(action, description)


def retry_select(locator, value, description):
    def action():
        locator.wait_for(state="visible", timeout=3000)
        locator.select_option(value=value)
        expect(locator).to_have_value(value)

    retry_action(action, description)


def assert_step_state(page, current_step):
    for step_num in (1, 2, 3):
        step = page.get_by_test_id(f"step-{step_num}")
        progress = page.locator(f"#prog-{step_num}")

        expected_step_class = "step active" if step_num == current_step else "step"
        expected_progress_class = (
            "progress-step active" if step_num <= current_step else "progress-step"
        )

        expect(step).to_have_class(expected_step_class)
        expect(progress).to_have_class(expected_progress_class)


def main():
    html_path = Path(__file__).with_name("form.html").resolve()
    url = html_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        expect(page.get_by_test_id("form-container")).to_be_visible()
        expect(page.get_by_test_id("progress-bar")).to_be_visible()

        assert_step_state(page, 1)

        retry_fill(page.get_by_test_id("fullname"), TEST_DATA["full_name"], "fill full name")
        retry_fill(page.get_by_test_id("email"), TEST_DATA["email"], "fill email")
        retry_fill(page.get_by_test_id("phone"), TEST_DATA["phone"], "fill phone")
        retry_click(page.get_by_test_id("next-1"), "go to step 2")

        assert_step_state(page, 2)

        retry_fill(page.get_by_test_id("street"), TEST_DATA["street"], "fill street")
        retry_fill(page.get_by_test_id("city"), TEST_DATA["city"], "fill city")
        retry_select(page.get_by_test_id("state"), TEST_DATA["state"], "select state")
        retry_fill(page.get_by_test_id("zip"), TEST_DATA["zip"], "fill ZIP code")
        retry_click(page.get_by_test_id("next-2"), "go to step 3")

        assert_step_state(page, 3)

        expect(page.get_by_test_id("review-fullname")).to_have_text(TEST_DATA["full_name"])
        expect(page.get_by_test_id("review-email")).to_have_text(TEST_DATA["email"])
        expect(page.get_by_test_id("review-phone")).to_have_text(TEST_DATA["phone"])
        expect(page.get_by_test_id("review-address")).to_have_text(
            f"{TEST_DATA['street']}, {TEST_DATA['city']}, {TEST_DATA['state']} {TEST_DATA['zip']}"
        )

        retry_click(page.get_by_test_id("submit"), "submit registration")

        success_panel = page.get_by_test_id("success-panel")
        submission_id = page.get_by_test_id("submission-id")

        expect(success_panel).to_be_visible()
        expect(submission_id).to_be_visible()
        expect(submission_id).to_have_text(re.compile(r"REG-[A-Z0-9]{8}"))

        page.screenshot(path="success.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except PlaywrightTimeoutError as exc:
        raise SystemExit(f"Playwright timed out: {exc}")
