import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

driver_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../chromedriver/chromedriver"))
service = Service(driver_path)


def test_weather_page_loads():
    driver = webdriver.Chrome(service=service)

    driver.get("http://localhost")

    time.sleep(1)  

    assert "Weather" in driver.title or "תחזית" in driver.title

    driver.quit()
