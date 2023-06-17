from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium_stealth import stealth
import time
import os

def get_driver(headless=True):
    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    prefs = {
        "profile.default_content_settings.popups": 0,
        "download.default_directory": os.path.join(os.getcwd(), 'downloads'),#IMPORTANT - ENDING SLASH V IMPORTANT
        "directory_upgrade": True
    }  
    options.add_experimental_option("prefs", prefs)
    options.add_extension('./adblocker.crx')

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    if headless:
        options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--user-data-dir=C:\environments\selenium")
    options.add_argument("--no-sandbox")  # Disable the sandbox
    options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage
    options.add_argument("--disable-infobars")  # Disable the "Chrome is being controlled by automated test software" notification
    options.add_argument("--disable-notifications")  # Disable notifications
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")  # Set a custom user agent

    driver = webdriver.Chrome(options=options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

def click_when_clickable(driver, selector, sel_type, timeout=10, repeated=False):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((sel_type, selector))
        )
        element.click()
        return element
    except TimeoutException:
        return False
    except ElementClickInterceptedException:
        if repeated:
            print('Tried twice, sorry not sorry...')
            return False
        
        print('Something is in the way lol hopefully sleep and thatll fix it')
        time.sleep(1)
        click_when_clickable(driver, selector, sel_type, timeout, True)
        

def wait_for_element_clickable(driver, element, timeout=10, repeated=True):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(element)
    )

def wait_for_element(driver, selector, sel_type, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((sel_type, selector))
    )

def find_element(driver, selector, sel_type):
    try:
        return driver.find_element(sel_type, selector)
    except NoSuchElementException:
        return False
