import os
import time
from playwright.sync_api import sync_playwright, expect

def run_test():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Get absolute path to form.html
        file_path = "file://" + os.path.abspath("form.html")
        page.goto(file_path)

        def retry_action(action, retries=3, delay=1):
            """Helper to retry interactions with a short delay."""
            for i in range(retries):
                try:
                    return action()
                except Exception as e:
                    if i == retries - 1:
                        raise e
                    print(f"Action failed, retrying ({i+1}/{retries})...")
                    time.sleep(delay)

        # --- Step 1: Personal Info ---
        print("Starting Step 1...")
        expect(page.get_by_test_id("step-1")).to_be_visible()
        expect(page.locator("#prog-1")).to_have_class("progress-step active")
        
        retry_action(lambda: page.get_by_test_id("fullname").fill("John Doe"))
        retry_action(lambda: page.get_by_test_id("email").fill("john@example.com"))
        retry_action(lambda: page.get_by_test_id("phone").fill("555-0199"))
        retry_action(lambda: page.get_by_test_id("next-1").click())

        # --- Step 2: Address ---
        print("Starting Step 2...")
        expect(page.get_by_test_id("step-2")).to_be_visible()
        expect(page.locator("#prog-2")).to_have_class("progress-step active")

        retry_action(lambda: page.get_by_test_id("street").fill("123 Playwright Way"))
        retry_action(lambda: page.get_by_test_id("city").fill("San Francisco"))
        retry_action(lambda: page.get_by_test_id("state").select_option("CA"))
        retry_action(lambda: page.get_by_test_id("zip").fill("94105"))
        retry_action(lambda: page.get_by_test_id("next-2").click())

        # --- Step 3: Review & Submit ---
        print("Starting Step 3...")
        expect(page.get_by_test_id("step-3")).to_be_visible()
        expect(page.locator("#prog-3")).to_have_class("progress-step active")

        # Verify summary data
        expect(page.get_by_test_id("review-fullname")).to_have_text("John Doe")
        expect(page.get_by_test_id("review-email")).to_have_text("john@example.com")
        expect(page.get_by_test_id("review-phone")).to_have_text("555-0199")
        expect(page.get_by_test_id("review-address")).to_contain_text("123 Playwright Way, San Francisco, CA 94105")

        retry_action(lambda: page.get_by_test_id("submit").click())

        # --- Success State ---
        print("Verifying Success State...")
        success_panel = page.get_by_test_id("success-panel")
        expect(success_panel).to_be_visible()
        
        submission_id = page.get_by_test_id("submission-id")
        expect(submission_id).not_to_be_empty()
        print(f"Submission successful! ID: {submission_id.inner_text()}")

        # Save screenshot
        page.screenshot(path="success.png")
        print("Screenshot saved to success.png")

        browser.close()

if __name__ == "__main__":
    run_test()
