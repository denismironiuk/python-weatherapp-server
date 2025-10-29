import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

@pytest.fixture
def driver():
    """
    Pytest fixture that initializes the Chrome WebDriver with cache disabled and incognito mode.
    Ensures the browser is properly closed after each test.
    """
    service = Service("/home/den4ik/python/PyLint/chromedriver/chromedriver")
    options = webdriver.ChromeOptions()

    # options.add_argument('--headless')  # Uncomment to run in headless mode
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

BASE_URL = "http://localhost"
TIMEOUT = 10

def test_valid_location_response(driver):
    """
    ✅ Positive Test: Valid country and city input should return weather forecast cards.
    """
    driver.get(BASE_URL)
    WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.NAME, "country"))).send_keys("Israel")
    driver.find_element(By.NAME, "city").send_keys("Tel Aviv")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    forecast_cards = WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "forecast-card"))
    )
    assert len(forecast_cards) > 0, "Expected forecast cards to be displayed for valid input."


def test_invalid_location_response(driver):
    """
    ❌ Negative Test: Invalid city input should trigger an error message.
    """
    driver.get(BASE_URL)
    WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.NAME, "country"))).send_keys("Israel")
    driver.find_element(By.NAME, "city").send_keys("InvalidCity")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    error_element = WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_element_located((By.CLASS_NAME, "error"))
    )
    assert "location not found" in error_element.text.lower(), "Expected error message for invalid location."


def test_special_characters_input(driver):
    """
    ❌ Negative Test: Country and city with special characters should trigger an error.
    """
    driver.get(BASE_URL)
    driver.find_element(By.NAME, "country").send_keys("Isr@el")
    driver.find_element(By.NAME, "city").send_keys("Tel&Aviv")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    try:
        error_element = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error"))
        )
        assert "not found" in error_element.text.lower()
    except NoSuchElementException:
        pytest.fail("Expected error for special characters input.")


def test_case_insensitive_input(driver):
    """
    ✅ Positive Test: Inputs should be case-insensitive and return valid forecast.
    """
    driver.get(BASE_URL)
    driver.find_element(By.NAME, "country").send_keys("isRaEL")
    driver.find_element(By.NAME, "city").send_keys("tEl aVIV")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    heading = WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_element_located((By.TAG_NAME, "h2"))
    )
    heading_text = heading.text.lower()
    assert "tel aviv" in heading_text and "israel" in heading_text, "Case-insensitive input should work."
