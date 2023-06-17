import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from selenium_utils import get_driver, click_when_clickable, wait_for_element, find_element
load_dotenv()

COOKIES_FILE = "cookies.pkl"
USER = os.getenv('USER')
PASSWORD = os.getenv('PASS')
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

def reload_session(driver, username, password):
    driver.get(GUIDE_URL)

    login_btn = click_when_clickable(driver, 'login', By.ID, 1)
    if login_btn:
        print('Re-authenticating')
        if os.path.exists(COOKIES_FILE):
            cookies = pickle.load(open(COOKIES_FILE, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
        
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
            
        # let everything settle a bit
        time.sleep(1)
    else:
        print('Profile was saved, no authentication required')

def get_mod_links(driver):
    container_names = [
        'General',
        'Combat Mods',
        'Character',
        'Overhauls',
        'Graphics',
        'Magic Mods',
        'Leveling and Skills',
        'Race and Birthsign Mods',
    ]
    safe_links = {}
    unused_links = {}
    for name in container_names:
        xpath = f"//*[text()='{name}']/../../../following-sibling::div[contains(@class, 'bbc_spoiler')]"
        mod_container = driver.find_element(By.XPATH, xpath)

        # todo - fix this lol
        mod_links = mod_container.find_elements(By.CSS_SELECTOR, 'br + br + a')
        pattern = r'(https:\/\/www\.nexusmods\.com\/oblivion\/mods\/\d+)'
        
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

        # click on the download button
        click_when_clickable(driver, "//span[text()='Manual']", By.XPATH)

        # check if the extra download dialog as appeared
        if find_element(driver, '.mfp-content', By.CSS_SELECTOR):
            # click the button to continue
            click_when_clickable(driver, "//a[text()='Download']", By.XPATH)

        # can only download single files, no way to choose between multiples
        if not 'file_id=' in driver.current_url:
            print(f'Multiple download options available - {name}')
            skipped_links.update({name:href})
            continue
        
        print(f"Downloading mod - {name}")
        # click on the 'Slow Download' button (no premium sad)
        click_when_clickable(driver, 'slowDownloadButton', By.ID)
        # minimum wait time for downloads to start is 5 seconds
        # provide an extra second to be safe
        time.sleep(6)
        
    ctr = 0 
    while(not is_download_finished('./downloads')):
        ctr +=1
        print(f'waiting downloads to finish ({ctr})')
        time.sleep(10)

if __name__ == "__main__":
    driver = get_driver(headless=True)
    print('Authenticating')
    reload_session(driver, USER, PASSWORD)

    assert driver.current_url == GUIDE_URL
    print('On the guide page, getting links')
    safe_links, unused_links = get_mod_links(driver)

    download_mods(safe_links)
        


        
