Windows:
* python3 -m venv myvenv
* myvenv\Scripts\activate
* python -m pip install -r requirements.txt
* place chromedriver.exe at the root directory (download: https://chromedriver.chromium.org/downloads)
* rename `local_settings_example.py` to `local_settings.py` and enter all the credentials
* python3 interface.py

Windows cmd:
* chrome.exe --remote-debugging-port=1111 --user-data-dir="C:\selenum\AutomationProfile"

local development:
* chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:1111")  # NB: uncomment when you test it

prod development:
* chrome_options.add_experimental_option('useAutomationExtension', False)  # NB: uncommment when you publish it
* chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])  # NB: uncommment when you publish it
* chrome_options.add_experimental_option("prefs", {
*     "profile.default_content_setting_values.notifications": 2,
* })  # NB: uncommment when you publish it

In order to publish app:
* pyinstaller interface.py --onefile

Search for `interface.exe` file in the `dist` directory
