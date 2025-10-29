import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
import time


@pytest.fixture
def driver():
    # הנתיב ל־chromedriver שנמצא בתוך הפרויקט
    service = Service(service = Service("/home/den4ik/python/PyLint/chromedriver/chromedriver")
)
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()


# ✅ Positive Test: בדיקה שמיקום קיים מחזיר תחזית
def test_valid_location_response(driver):
    driver.get("http://localhost")  # אם nginx מקשיב על פורט 80
    time.sleep(1)

    country_input = driver.find_element(By.NAME, "country")
    city_input = driver.find_element(By.NAME, "city")
    submit_button = driver.find_element(By.TAG_NAME, "button")

    country_input.send_keys("Israel")
    city_input.send_keys("Tel Aviv")
    submit_button.click()

    time.sleep(2)



# ❌ Negative Test: בדיקה למיקום שגוי
def test_invalid_location_response(driver):
    driver.get("http://localhost")
    time.sleep(1)

    driver.find_element(By.NAME, "country").send_keys("Israel")
    driver.find_element(By.NAME, "city").send_keys("Haifa")
    driver.find_element(By.TAG_NAME, "button").click()

    time.sleep(2)

