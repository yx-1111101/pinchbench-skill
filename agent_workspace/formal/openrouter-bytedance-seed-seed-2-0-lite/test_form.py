from pathlib import Path
import re
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


FORM_DATA = {
    "fullname": "Jordan Lee",
    "email": "jordan.lee@example.com",
    "phone": "+1 555-123-4567",
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102",
}


def retry_action(action, description, retries=3, delay=0.4):
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


def fill_with_retry(locator, value, description):
    retry_action(lambda: locator.fill(value), f"fill {description}")
    expect(locator).to_have_value(value)


def click_with_retry(locator, description):
    retry_action(lambda: locator.click(), f"click {description}")


def select_with_retry(locator, value, description):
    retry_action(lambda: locator.select_option(value=value), f"select {description}")
    expect(locator).to_have_value(value)


def assert_step_state(page, active_step):
    for step in range(1, 4):
        step_locator = page.get_by_test_id(f"step-{step}")
        progress_locator = page.locator(f"#prog-{step}")

        if step == active_step:
            expect(step_locator).to_have_class(re.compile(r"\bactive\b"))
            expect(progress_locator).to_have_class(re.compile(r"\bactive\b"))
        else:
            expect(step_locator).not_to_have_class(re.compile(r"\bactive\b"))
            if step < active_step:
                expect(progress_locator).to_have_class(re.compile(r"\bactive\b"))
            else:
                expect(progress_locator).not_to_have_class(re.compile(r"\bactive\b"))


def main():
    form_path = Path(__file__).with_name("form.html").resolve()
    form_url = form_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(form_url, wait_until="domcontentloaded")

        expect(page.get_by_test_id("form-container")).to_be_visible()
        expect(page.get_by_test_id("progress-bar")).to_be_visible()
        assert_step_state(page, 1)

        fill_with_retry(page.get_by_test_id("fullname"), FORM_DATA["fullname"], "full name")
        fill_with_retry(page.get_by_test_id("email"), FORM_DATA["email"], "email")
        fill_with_retry(page.get_by_test_id("phone"), FORM_DATA["phone"], "phone")
        click_with_retry(page.get_by_test_id("next-1"), "step 1 next button")

        assert_step_state(page, 2)

        fill_with_retry(page.get_by_test_id("street"), FORM_DATA["street"], "street")
        fill_with_retry(page.get_by_test_id("city"), FORM_DATA["city"], "city")
        select_with_retry(page.get_by_test_id("state"), FORM_DATA["state"], "state")
        fill_with_retry(page.get_by_test_id("zip"), FORM_DATA["zip"], "zip")
        click_with_retry(page.get_by_test_id("next-2"), "step 2 next button")

        assert_step_state(page, 3)

        expect(page.get_by_test_id("review-fullname")).to_have_text(FORM_DATA["fullname"])
        expect(page.get_by_test_id("review-email")).to_have_text(FORM_DATA["email"])
        expect(page.get_by_test_id("review-phone")).to_have_text(FORM_DATA["phone"])
        expect(page.get_by_test_id("review-address")).to_have_text(
            f"{FORM_DATA['street']}, {FORM_DATA['city']}, {FORM_DATA['state']} {FORM_DATA['zip']}"
        )

        click_with_retry(page.get_by_test_id("submit"), "submit button")

        success_panel = page.get_by_test_id("success-panel")
        expect(success_panel).to_be_visible()
        submission_id = page.get_by_test_id("submission-id")
        expect(submission_id).to_be_visible()
        expect(submission_id).to_have_text(re.compile(r"^REG-[A-Z0-9]{8}$"))

        page.screenshot(path="success.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except PlaywrightTimeoutError as exc:
        raise SystemExit(f"Playwright timeout: {exc}") from exc
