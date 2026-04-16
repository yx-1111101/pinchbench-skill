from pathlib import Path
import re
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.4

TEST_DATA = {
    "fullname": "Jordan Smith",
    "email": "jordan.smith@example.com",
    "phone": "+1 555-123-4567",
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "state_label": "California",
    "zip": "94102",
}


def with_retry(action, selector: str):
    last_error = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == RETRY_ATTEMPTS:
                break
            time.sleep(RETRY_DELAY_SECONDS)
    raise AssertionError(
        f"Action failed for selector '{selector}' after {RETRY_ATTEMPTS} attempts"
    ) from last_error



def fill_with_retry(page, selector: str, value: str):
    with_retry(lambda: page.get_by_test_id(selector).fill(value), selector)



def click_with_retry(page, selector: str):
    with_retry(lambda: page.get_by_test_id(selector).click(), selector)



def select_with_retry(page, selector: str, value: str):
    with_retry(lambda: page.get_by_test_id(selector).select_option(value=value), selector)



def assert_step_state(page, active_step: int):
    for step in range(1, 4):
        locator = page.get_by_test_id(f"step-{step}")
        expected_class = re.compile(r"\bactive\b") if step == active_step else re.compile(r"^(?!.*\bactive\b).*$")
        expect(locator).to_have_class(expected_class)

    progress_steps = [page.locator(f"#prog-{i}") for i in range(1, 4)]
    for index, locator in enumerate(progress_steps, start=1):
        expected_class = re.compile(r"\bactive\b") if index <= active_step else re.compile(r"^(?!.*\bactive\b).*$")
        expect(locator).to_have_class(expected_class)



def main():
    form_path = Path(__file__).with_name("form.html").resolve()
    screenshot_path = Path(__file__).with_name("success.png")
    form_url = form_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(form_url, wait_until="domcontentloaded")

        expect(page.get_by_test_id("form-container")).to_be_visible()
        expect(page.get_by_test_id("progress-bar")).to_be_visible()

        # Step 1
        assert_step_state(page, 1)
        fill_with_retry(page, "fullname", TEST_DATA["fullname"])
        fill_with_retry(page, "email", TEST_DATA["email"])
        fill_with_retry(page, "phone", TEST_DATA["phone"])
        click_with_retry(page, "next-1")

        # Step 2
        assert_step_state(page, 2)
        fill_with_retry(page, "street", TEST_DATA["street"])
        fill_with_retry(page, "city", TEST_DATA["city"])
        select_with_retry(page, "state", TEST_DATA["state"])
        fill_with_retry(page, "zip", TEST_DATA["zip"])
        click_with_retry(page, "next-2")

        # Step 3
        assert_step_state(page, 3)
        expect(page.get_by_test_id("review-fullname")).to_have_text(TEST_DATA["fullname"])
        expect(page.get_by_test_id("review-email")).to_have_text(TEST_DATA["email"])
        expect(page.get_by_test_id("review-phone")).to_have_text(TEST_DATA["phone"])
        expect(page.get_by_test_id("review-address")).to_have_text(
            f"{TEST_DATA['street']}, {TEST_DATA['city']}, {TEST_DATA['state']} {TEST_DATA['zip']}"
        )
        click_with_retry(page, "submit")

        # Success panel
        expect(page.get_by_test_id("success-panel")).to_be_visible()
        submission_id = page.get_by_test_id("submission-id")
        expect(submission_id).to_have_text(re.compile(r"^REG-[A-Z0-9]{8}$"))
        page.screenshot(path=str(screenshot_path), full_page=True)

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"Playwright timed out: {exc}") from exc
