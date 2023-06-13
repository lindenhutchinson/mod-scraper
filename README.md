# Scraping Project

1. Create virtualenv. Install requirements.
```
virtualenv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

2. Download chromedriver - https://chromedriver.chromium.org/downloads
3. Download adblocker crx
    - https://crxextractor.com/
    - https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm 
    - rename file to adblocker.crx

4. Create a .env file with USER, PASSWORD and GUIDE_URL values
5. Run `main.py`