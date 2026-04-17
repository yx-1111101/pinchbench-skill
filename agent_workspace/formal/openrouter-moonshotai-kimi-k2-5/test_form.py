from pathlib import Path
import re
import time

from playwright.sync_api import expect, sync_playwright


FULL_NAME = "Jordan Lee"
EMAIL = "jordan.lee@example.com"
PHONE = "+1 555-123-4567"
STREET = "123 Main St"
CITY = "San Francisco"
STATE = "CA"
ZIP_CODE = "94102"


def retry(action, description, attempts=3, delay=0.4):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                raise AssertionError(
                    f"Failed {description} after {attempts} attempts"
                ) from exc
            time.sleep(delay)
    raise last_error


def tid(page, testid):
    return page.get_by_test_id(testid)


def click_with_retry(page, testid):
    retry(lambda: tid(page, testid).click(), f"click {testid}")


def fill_with_retry(page, testid, value):
    retry(lambda: tid(page, testid).fill(value), f"fill {testid}")


def select_with_retry(page, testid, value):
    retry(lambda: tid(page, testid).select_option(value=value), f"select {testid}")


def assert_step_state(page, active_step):
    for step in range(1, 4):
        locator = tid(page, f"step-{step}")
        if step == active_step:
            expect(locator).to_be_visible()
            retry(
                lambda: expect(locator).to_have_class(re.compile(r"\bactive\b")),
                f"verify step-{step} active",
            )
        else:
            expect(locator).not_to_be_visible()
            retry(
                lambda: expect(locator).not_to_have_class(re.compile(r"\bactive\b")),
                f"verify step-{step} inactive",
            )

    for step in range(1, 4):
        progress = page.locator(f"#prog-{step}")
        if step <= active_step:
            retry(
                lambda: expect(progress).to_have_class(re.compile(r"\bactive\b")),
                f"verify prog-{step} active",
            )
        else:
            retry(
                lambda: expect(progress).not_to_have_class(re.compile(r"\bactive\b")),
                f"verify prog-{step} inactive",
            )


def main():
    form_path = Path(__file__).with_name("form.html").resolve()
    form_url = form_path.as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        retry(lambda: page.goto(form_url, wait_until="domcontentloaded"), "navigate to form")
        expect(tid(page, "form-container")).to_be_visible()

        assert_step_state(page, 1)
        fill_with_retry(page, "fullname", FULL_NAME)
        fill_with_retry(page, "email", EMAIL)
        fill_with_retry(page, "phone", PHONE)
        click_with_retry(page, "next-1")

        assert_step_state(page, 2)
        fill_with_retry(page, "street", STREET)
        fill_with_retry(page, "city", CITY)
        select_with_retry(page, "state", STATE)
        fill_with_retry(page, "zip", ZIP_CODE)
        click_with_retry(page, "next-2")

        assert_step_state(page, 3)
        expect(tid(page, "review-fullname")).to_have_text(FULL_NAME)
        expect(tid(page, "review-email")).to_have_text(EMAIL)
        expect(tid(page, "review-phone")).to_have_text(PHONE)
        expect(tid(page, "review-address")).to_have_text(
            f"{STREET}, {CITY}, {STATE} {ZIP_CODE}"
        )

        click_with_retry(page, "submit")

        success_panel = tid(page, "success-panel")
        retry(lambda: expect(success_panel).to_be_visible(), "verify success panel visible")
        submission_id = tid(page, "submission-id")
        retry(
            lambda: expect(submission_id).to_have_text(re.compile(r"^REG-[A-Z0-9]{8}$")),
            "verify submission id",
        )

        page.screenshot(path="success.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
