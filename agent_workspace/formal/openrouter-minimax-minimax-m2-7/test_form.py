import re
from pathlib import Path
from time import sleep

from playwright.sync_api import expect, sync_playwright


TEST_DATA = {
    "fullname": "Jordan Lee",
    "email": "jordan.lee@example.com",
    "phone": "+1 555-123-4567",
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102",
}


def retry_action(action, description, attempts=3, delay=0.4):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as error:
            last_error = error
            if attempt == attempts:
                raise RuntimeError(
                    f"Failed to {description} after {attempts} attempts"
                ) from error
            sleep(delay)
    raise last_error


def locator_by_testid(page, testid):
    return page.get_by_test_id(testid)


def fill_with_retry(page, testid, value):
    retry_action(lambda: locator_by_testid(page, testid).fill(value), f"fill {testid}")


def click_with_retry(page, testid):
    retry_action(lambda: locator_by_testid(page, testid).click(), f"click {testid}")


def select_with_retry(page, testid, value):
    retry_action(
        lambda: locator_by_testid(page, testid).select_option(value),
        f"select {testid}",
    )


def expect_visible_with_retry(page, testid):
    retry_action(lambda: expect(locator_by_testid(page, testid)).to_be_visible(), f"verify {testid} visible")


def expect_text_with_retry(page, testid, value):
    retry_action(lambda: expect(locator_by_testid(page, testid)).to_have_text(value), f"verify {testid} text")


def assert_step_state(page, active_step):
    for step in range(1, 4):
        step_locator = locator_by_testid(page, f"step-{step}")
        progress_locator = page.locator(f"#prog-{step}")

        if step == active_step:
            retry_action(lambda: expect(step_locator).to_be_visible(), f"verify step-{step} visible")
        else:
            retry_action(lambda: expect(step_locator).to_be_hidden(), f"verify step-{step} hidden")

        if step <= active_step:
            retry_action(
                lambda: expect(progress_locator).to_have_class(re.compile(r".*active.*")),
                f"verify prog-{step} active",
            )
        else:
            retry_action(
                lambda: expect(progress_locator).not_to_have_class(re.compile(r".*active.*")),
                f"verify prog-{step} inactive",
            )


def main():
    form_path = Path(__file__).with_name("form.html").resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(form_path)

        expect_visible_with_retry(page, "form-container")
        assert_step_state(page, active_step=1)

        fill_with_retry(page, "fullname", TEST_DATA["fullname"])
        fill_with_retry(page, "email", TEST_DATA["email"])
        fill_with_retry(page, "phone", TEST_DATA["phone"])
        click_with_retry(page, "next-1")

        assert_step_state(page, active_step=2)

        fill_with_retry(page, "street", TEST_DATA["street"])
        fill_with_retry(page, "city", TEST_DATA["city"])
        select_with_retry(page, "state", TEST_DATA["state"])
        fill_with_retry(page, "zip", TEST_DATA["zip"])
        click_with_retry(page, "next-2")

        assert_step_state(page, active_step=3)

        expect_text_with_retry(page, "review-fullname", TEST_DATA["fullname"])
        expect_text_with_retry(page, "review-email", TEST_DATA["email"])
        expect_text_with_retry(page, "review-phone", TEST_DATA["phone"])
        expect_text_with_retry(
            page,
            "review-address",
            f"{TEST_DATA['street']}, {TEST_DATA['city']}, {TEST_DATA['state']} {TEST_DATA['zip']}",
        )

        click_with_retry(page, "submit")

        expect_visible_with_retry(page, "success-panel")
        submission_id = locator_by_testid(page, "submission-id")
        retry_action(
            lambda: expect(submission_id).to_have_text(re.compile(r"REG-[A-Z0-9]{8}")),
            "verify submission id",
        )
        page.screenshot(path="success.png", full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
