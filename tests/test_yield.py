"""
Selenium test — validates 60% yield for part 001PN001.

Usage:
    python static/test_yield.py [http://localhost:8000]
"""

import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
EXPECTED_YIELD = "60%"
PART_NUMBER = "001PN001"
RECORDS = [
    {"serial": "SN-T001", "status": True},   # pass
    {"serial": "SN-T002", "status": True},   # pass
    {"serial": "SN-T003", "status": True},   # pass
    {"serial": "SN-T004", "status": False},  # fail
    {"serial": "SN-T005", "status": False},  # fail
]


def run():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        print(f"Opening dashboard: {BASE_URL}")
        driver.get(BASE_URL)

        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "manual-test-btn")))

        # Insert 5 records
        for i, record in enumerate(RECORDS, 1):
            # Open modal
            manual_btn = wait.until(EC.element_to_be_clickable((By.ID, "manual-test-btn")))
            driver.execute_script("arguments[0].click();", manual_btn)

            # Wait for modal to be visible
            wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))

            # Fill serial number
            sn_input = driver.find_element(By.ID, "serial-number")
            sn_input.clear()
            sn_input.send_keys(record["serial"])

            # Select part number
            pn_select = Select(driver.find_element(By.ID, "part-number"))
            pn_select.select_by_value(PART_NUMBER)

            # Set status checkbox
            checkbox = driver.find_element(By.ID, "status")
            current_checked = checkbox.is_selected()
            if record["status"] != current_checked:
                driver.execute_script("arguments[0].click();", checkbox)

            # Submit
            add_btn = driver.find_element(By.ID, "add-test-btn")
            driver.execute_script("arguments[0].click();", add_btn)

            # Wait for success message
            wait.until(lambda d: "Record added" in d.find_element(By.ID, "modal-message").text)
            print(f"  Record {i}/5 inserted ({'PASS' if record['status'] else 'FAIL'}): {record['serial']}")

            # Close modal
            close_btn = driver.find_element(By.ID, "close-modal-btn")
            driver.execute_script("arguments[0].click();", close_btn)

            # Wait for modal to close
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#manual-modal.open")))
            time.sleep(0.3)

        # Click the part number chip to select 001PN001
        print(f"\nSelecting part number: {PART_NUMBER}")
        part_btn = wait.until(EC.element_to_be_clickable((By.ID, f"part-{PART_NUMBER}")))
        driver.execute_script("arguments[0].click();", part_btn)

        # Wait for gauge to update
        time.sleep(1.5)

        # Read yield value
        yield_el = wait.until(EC.visibility_of_element_located((By.ID, "yield-value")))
        actual_yield = yield_el.text.strip()

        # Report
        print(f"\nExpected yield: {EXPECTED_YIELD}")
        print(f"Actual yield:   {actual_yield}")

        if actual_yield == EXPECTED_YIELD:
            print("PASS")
        else:
            print("FAIL")

    finally:
        driver.quit()


if __name__ == "__main__":
    run()
