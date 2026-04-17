from pathlib import Path
import re
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


BASE_DIR = Path(__file__).resolve().parent
FORM_URL = BASE_DIR.joinpath("form.html").resolve().as_uri()
SCREENSHOT_PATH = BASE_DIR / "success.png"
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.5

TEST_DATA = {
    "fullname": "Jordan Smith",
    "email": "jordan.smith@example.com",
    "phone": "+1 555-123-4567",
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102",
}


def with_retry(action, description: str):
    last_error = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == RETRY_ATTEMPTS:
                raise AssertionError(
                    f"Failed after {RETRY_ATTEMPTS} attempts: {description}"
                ) from exc
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_error


def fill_with_retry(page, testid: str, value: str):
    with_retry(
        lambda: page.get_by_test_id(testid).fill(value),
        f"fill {testid}",
    )


def click_with_retry(page, testid: str):
    with_retry(
        lambda: page.get_by_test_id(testid).click(),
        f"click {testid}",
    )


def select_with_retry(page, testid: str, value: str):
    with_retry(
        lambda: page.get_by_test_id(testid).select_option(value=value),
        f"select {testid}={value}",
    )


def expect_step_state(page, active_step: int):
    for step in range(1, 4):
        locator = page.get_by_test_id(f"step-{step}")
        if step == active_step:
            expect(locator).to_have_class(re.compile(r"\bstep active\b|\bactive step\b"))
        else:
            expect(locator).not_to_have_class(re.compile(r"\bactive\b"))

    for progress in range(1, 4):
        locator = page.locator(f"#prog-{progress}")
        if progress <= active_step:
            expect(locator).to_have_class(re.compile(r"\bactive\b"))
        else:
            expect(locator).not_to_have_class(re.compile(r"\bactive\b"))


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(FORM_URL, wait_until="domcontentloaded")
            expect(page.get_by_test_id("form-container")).to_be_visible()

            expect_step_state(page, 1)
            fill_with_retry(page, "fullname", TEST_DATA["fullname"])
            fill_with_retry(page, "email", TEST_DATA["email"])
            fill_with_retry(page, "phone", TEST_DATA["phone"])
            click_with_retry(page, "next-1")

            expect_step_state(page, 2)
            fill_with_retry(page, "street", TEST_DATA["street"])
            fill_with_retry(page, "city", TEST_DATA["city"])
            select_with_retry(page, "state", TEST_DATA["state"])
            fill_with_retry(page, "zip", TEST_DATA["zip"])
            click_with_retry(page, "next-2")

            expect_step_state(page, 3)
            expect(page.get_by_test_id("review-fullname")).to_have_text(TEST_DATA["fullname"])
            expect(page.get_by_test_id("review-email")).to_have_text(TEST_DATA["email"])
            expect(page.get_by_test_id("review-phone")).to_have_text(TEST_DATA["phone"])
            expect(page.get_by_test_id("review-address")).to_have_text(
                f"{TEST_DATA['street']}, {TEST_DATA['city']}, {TEST_DATA['state']} {TEST_DATA['zip']}"
            )

            click_with_retry(page, "submit")

            success_panel = page.get_by_test_id("success-panel")
            expect(success_panel).to_be_visible()
            submission_id = page.get_by_test_id("submission-id")
            expect(submission_id).to_be_visible()
            expect(submission_id).to_have_text(re.compile(r"^REG-[A-Z0-9]{8}$"))

            with_retry(
                lambda: page.screenshot(path=str(SCREENSHOT_PATH), full_page=True),
                "save success screenshot",
            )
        finally:
            browser.close()


if __name__ == "__main__":
    main()
