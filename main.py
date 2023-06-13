from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import re
from selenium_stealth import stealth
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

COOKIES_FILE = "cookies.pkl"
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
GUIDE_URL = os.getenv('GUIDE_URL')

def is_download_finished(temp_folder):
    firefox_temp_file = sorted(Path(temp_folder).glob('*.part'))
    chrome_temp_file = sorted(Path(temp_folder).glob('*.crdownload'))
    downloaded_files = sorted(Path(temp_folder).glob('*.*'))
    if (len(firefox_temp_file) == 0) and \
       (len(chrome_temp_file) == 0) and \
       (len(downloaded_files) >= 1):
        return True
    else:
        return False

def login(driver, username, password):
    # Find the username input element by ID and enter the username
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user_login"))
    )
    username_input.send_keys(username)

    # Find the password input element by ID and enter the password
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    password_input.send_keys(password)

    # Find the login button by name and click on it
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "commit"))
    )
    login_button.click()

def wait_for_clickable(driver, selector, sel_type, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((sel_type, selector))
        )
    except TimeoutException:
        return False

def wait_for_element_clickable(driver, element, timeout=10):
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

def reload_session(driver, username, password):
    driver.get(GUIDE_URL)

    login_btn =  wait_for_clickable(driver, 'login', By.ID, 3)
    if login_btn:
        print('Re-authenticating')
        if os.path.exists(COOKIES_FILE):
            cookies = pickle.load(open(COOKIES_FILE, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
        login_btn.click()
        
        if find_element(driver, 'new_user', By.ID):
            # we have landed on the login page - cookies are probably expired
            login(driver, username, password)
            # save the cookies after logging in
            pickle.dump(driver.get_cookies(), open(COOKIES_FILE, "wb"))
        else:
            # cookies have loaded
            # but we still need to confirm the authentication
            continue_btn = wait_for_element(driver, 'a.btn.btn-primary', By.CSS_SELECTOR)
            continue_btn.click()
    else:
        print('Profile was saved, no authentication required')

    # wait for all the login actions to settle
    time.sleep(1)

def get_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    prefs = {
        "profile.default_content_settings.popups": 0,
        "download.default_directory": r'./downloads//',#IMPORTANT - ENDING SLASH V IMPORTANT
        "directory_upgrade": True
    }  
    options.add_extension('./adblocker.crx')

    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
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

def get_mod_links(driver):
    container_names = [
        'Core Mods',
        'Character',
        'Overhauls',
        'Graphics',
        'Combat Mods',
        'Magic Mods',
        'Leveling and Skills',
        'Race and Birthsign Mods',
        'General',
    ]

    for name in container_names:
        xpath = f"//*[text()='{name}']/../../../following-sibling::div[contains(@class, 'bbc_spoiler')]"
        mod_container = driver.find_element(By.XPATH, xpath)

        # todo - fix this lol
        mod_links = mod_container.find_elements(By.CSS_SELECTOR, 'br + br + a')
        pattern = r'(https:\/\/www\.nexusmods\.com\/oblivion\/mods\/\d+)'
        safe_links = {}
        unused_links = {}
        for link in mod_links:
            href = link.get_attribute('href')
            text = link.get_attribute('text')
            res = re.findall(pattern, href)
            if len(res):
                safe_links.update({text:href})
            else:
                unused_links.update({text:href})

    return safe_links, unused_links

def download_mods(links):
    skipped_links = {}
    print(f"Attempting to download {len(list(links))} mods")
    for name, href in links.items():
        driver.get(href)

        download_btn = wait_for_clickable(driver, "//span[text()='Manual']", By.XPATH)
        download_btn.click()

        # check if the extra download dialog as appeared
        if find_element(driver, '.mfp-content', By.CSS_SELECTOR):
            continue_btn = wait_for_clickable(driver, "//a[text()='Download']", By.XPATH)
            continue_btn.click()

        # can only download single files, no way to choose between multiples
        if not 'file_id=' in driver.current_url:
            print(f'Multiple download options available - {name}')
            skipped_links.update({name:href})
            continue
        
        print(f"Downloading mod - {name}")
        slow_dl_btn = wait_for_clickable(driver, 'slowDownloadButton', By.ID)
        slow_dl_btn.click()
        # minimum wait time for downloads to start is 5 seconds
        # provide an extra second to be safe
        time.sleep(6)

if __name__ == "__main__":
    driver = get_driver()

    reload_session(driver, USER, PASSWORD)

    assert driver.current_url == GUIDE_URL

    safe_links, unused_links = get_mod_links(driver)
    download_mods(safe_links)

    while(not is_download_finished('./downloads')):
        print('waiting for stuff to finish downloading')
        time.sleep(10)

        
