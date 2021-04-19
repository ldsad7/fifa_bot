import asyncio
import logging
import os
import platform
import random
import re
import sys
import time
import zipfile
from pathlib import Path
from selenium.webdriver.common.keys import Keys
from time import sleep
from random import choice
from yarl import URL

import selenium
from fake_useragent import UserAgent
# from proxybroker import Broker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from py_files.cookie import Cookie
# from py_files.move_mouse import ActionChainsChild

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.log"),
    level=logging.INFO
)
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))
COOKIE = 'cookie.txt'
MANIFEST_JSON = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""
BACKGROUND_JS = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
"""
PLUGIN_FILE = 'proxy_auth_plugin.zip'


class CustomUserAgent:
    browsers = {
        'chrome': r'Chrome/[^ ]+',
        'safari': r'AppleWebKit/[^ ]+',
        'opera': r'Opera\s.+$',
        'firefox': r'Firefox/.+$',
        'internetexplorer': r'Trident/[^;]+',
    }

    def __init__(self, user_agent=None, latest_version=True):
        self.latest_version = latest_version
        self.ua = UserAgent()
        if user_agent is None:
            user_agent = self.get_random_user_agent()
        else:
            try:
                user_agent = eval(f'user_agent.{user_agent}')
            except Exception:
                LOG.info(f'bad user agent "{user_agent}", switching to random')
                user_agent = self.get_random_user_agent()
            else:
                LOG.info('using the following User-Agent:', user_agent)
        LOG.info(f'user-agent: {user_agent}')
        self.user_agent = user_agent

    def get_random_user_agent(self):
        if self.latest_version:
            # browser = random.choice(self.ua.data_randomize)
            browser = 'chrome'
            user_agent = choice(sorted(
                self.ua.data_browsers[browser], key=lambda a: self.grp(self.browsers[browser], a)
            )[-20:])
        else:
            user_agent = self.ua.random
        return user_agent

    @staticmethod
    def grp(pat, txt):
        r = re.search(pat, txt)
        return r.group(0) if r else '&'


# class CustomProxy:
#     def __init__(self, proxy=None, countries=None, excluded_countries=None):
#         self.loop = asyncio.get_event_loop()
#         proxy_server = None
#         if proxy is not None:
#             if proxy is True:
#                 proxy = self.get_proxy(countries=countries, excluded_countries=excluded_countries)
#             url = URL(proxy)
#             if url.user:  # there should be authentication
#
#                 pass
#             else:
#                 proxy_server = proxy.split("://")[-1]
#                 LOG.info(f'proxy-server: {proxy_server}')
#                 self.proxy_server = proxy_server
#
#     def get_proxy(self, countries=None, excluded_countries=None):
#         pass
#         # proxies = asyncio.Queue()
#         # broker = Broker(proxies)
#         #
#         # countries = countries or frozenset()
#         # excluded_countries = excluded_countries or {'RU'}
#         # countries = list(countries - excluded_countries)
#         # tasks = asyncio.gather(
#         #     broker.find(types=['HTTP', 'HTTPS'], countries=countries, limit=1),
#         #     self.__async__get_proxy(proxies)
#         # )
#         # return self.loop.run_until_complete(tasks)[-1]
#
#     @staticmethod
#     async def __async__get_proxy(proxies):
#         while True:
#             proxy = await proxies.get()
#             if proxy is not None:
#                 proto = 'https' if 'HTTPS' in proxy.types else 'http'
#                 proxy = f'{proto}://{proxy.host}:{proxy.port}'
#                 LOG.info(f'Found proxy: {proxy}')
#                 return proxy


class CustomChromeOptions:
    def __init__(self, user_agent=None, exclude_switches=False, exclude_photos=False,
                 proxy=None, hide=False, countries=None, excluded_countries=None):
        chrome_options = webdriver.ChromeOptions()

        # USER_AGENT
        # user_agent = CustomUserAgent(user_agent=user_agent)
        # chrome_options.add_argument(f'--user-agent={user_agent.user_agent}')

        # PROXY
        # proxy = CustomProxy(proxy=proxy, countries=countries, excluded_countries=excluded_countries)
        # if proxy.proxy_server is not None:
        #     chrome_options.add_argument(f'--proxy-server={proxy.proxy_server}')
        if proxy is not None:
            url = URL(proxy)
            if url.user:  # there should be authentication
                with zipfile.ZipFile(PLUGIN_FILE, 'w') as zp:
                    zp.writestr("manifest.json", MANIFEST_JSON)
                    zp.writestr("background.js", BACKGROUND_JS % (url.host, url.port, url.user, url.password))
                chrome_options.add_extension(PLUGIN_FILE)
            else:
                proxy_server = proxy.split("://")[-1]
                LOG.info(f'proxy-server: {proxy_server}')
                chrome_options.add_argument(f'--proxy-server={proxy_server}')

        # EXCLUDE_SWITCHES
        if exclude_switches:
            chrome_options.add_experimental_option("excludeSwitches", [
                "disable-background-networking",
                "disable-client-side-phishing-detection",
                "disable-default-apps",
                "disable-hang-monitor",
                "disable-popup-blocking",
                "disable-prompt-on-repost",
                "enable-automation",
                "enable-blink-features=ShadowDOMV0",
                "enable-logging",
                "force-fieldtrials=SiteIsolationExtensions/Control",
                "load-extension=/var/folders/zz/zyxvpxvq6csfxvn_n0001_y8000_qk/T/.com.google.Chrome.HPBfiz/internal",
                "log-level=0",
                "password-store=basic",
                "remote-debugging-port=0",
                "test-type=webdriver",
                "use-mock-keychain",
                "user-data-dir=/var/folders/zz/zyxvpxvq6csfxvn_n0001_y8000_qk/T/.com.google.Chrome.drJGEY",
            ])

        # EXCLUDE_PHOTOS
        if exclude_photos:
            chrome_options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2
            })

        # EXPERIMENTAL_OPTIONS
        # chrome_options.add_experimental_option('useAutomationExtension', False)  # NB: uncommment when you publish it
        # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])  # NB: uncommment when you publish it
        # chrome_options.add_experimental_option("prefs", {
        #     "profile.default_content_setting_values.notifications": 2,
        # })  # NB: uncommment when you publish it
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:1111")  # NB: uncomment when you test it

        # ARGUMENTS
        chrome_options.add_argument('--profile-directory=Default')
        chrome_options.add_argument("--start-maximized")

        # HIDE
        if hide:
            chrome_options.add_argument('--headless')

        self.chrome_options = chrome_options


class Driver:
    def __init__(
            self, user_agent=None, proxy=None, hide=False, exclude_switches=False,
            exclude_photos=False, width=None, height=None, timeout=None, countries=None,
            excluded_countries=None, **kwargs):
        self.driver = None

        # CHROME_OPTIONS
        chrome_options = CustomChromeOptions(
            user_agent=user_agent, exclude_switches=exclude_switches,
            exclude_photos=exclude_photos, proxy=proxy, hide=hide,
            countries=countries, excluded_countries=excluded_countries,
        )

        # CHROMEDRIVER name
        os_platform = platform.system()
        # We need to add Linux here (ChromeDriver 83.0.4103.39 version)
        chromedriver = 'chromedriver.exe' if os_platform == 'Windows' else 'chromedriver'

        # INIT driver
        LOG.info("INITIALIZING DRIVER")
        driver = webdriver.Chrome(
            (Path.cwd() / chromedriver).name,
            options=chrome_options.chrome_options,
        )

        # # WINDOW_SIZE
        # width = width or random.randint(900, 1400)
        # height = height or random.randint(900, 1400)
        # driver.set_window_size(width, height)

        # ?
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """Object.defineProperty(navigator, 'webdriver',
                {get: () => undefined})"""
            }
        )

        # TIMEOUT
        if timeout is not None:
            driver.implicitly_wait(timeout)

        self.driver = driver

        # LOADING COOKIE
        self.cookie = Cookie(self.driver, COOKIE)
        self.driver.get('https://www.google.com')
        try:
            self.cookie.load_cookie()
        except Exception:
            pass

    def send(self, sel, text):
        """ send value 'text' to web element defined by selector """
        element = self.find_element_by_css_selector(sel)
        if not element.get_attribute('value'):
            element.send_keys(text)

    def get(self, link):
        """ get link from current page """
        self.driver.execute_script(f'window.location.href = "{link}";')

    def implicitly_wait(self, time_):
        self.driver.implicitly_wait(time_)

    def wait_until(self, css_selector, timeout=30, selector_type='css', captcha=False):
        if selector_type == 'css':
            selector_type = By.CSS_SELECTOR
        elif selector_type == 'id':
            selector_type = By.ID
        elif selector_type == 'xpath':
            selector_type = By.XPATH
        else:
            raise ValueError("Incorrect selector type")

        # CAPTCHA bypassing
        if captcha:
            if selector_type == 'css':
                WebDriverWait(self.driver, timeout).until(
                    ec.frame_to_be_available_and_switch_to_it((selector_type, css_selector))
                )
            elif selector_type == 'xpath':
                WebDriverWait(self.driver, timeout).until(
                    ec.element_to_be_clickable((selector_type, css_selector))
                )
        else:
            if selector_type == 'xpath':
                WebDriverWait(self.driver, timeout).until(
                    ec.element_to_be_clickable((selector_type, css_selector))
                )
            else:
                WebDriverWait(self.driver, timeout).until(
                    ec.visibility_of_element_located((selector_type, css_selector))
                )

    def expand_shadow_element(self, element):
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root

    def find_element_by_css_selector(self, sel):
        try:
            return self.driver.find_element_by_css_selector(sel)
        except selenium.common.exceptions.NoSuchElementException:
            return None

    def find_by_id(self, id_):
        try:
            return self.driver.find_element_by_id(id_)
        except selenium.common.exceptions.NoSuchElementException:
            return None

    def find_elements_by_css_selector(self, sel):
        return self.driver.find_elements_by_css_selector(sel)

    def click(self, sel):
        """ click on web element """
        self.find_element_by_css_selector(sel).click()

    # def mouse_click(self):
    #     ActionChainsChild(self.driver).click().perform()

    def get_user_agent(self):
        return self.driver.execute_script("return navigator.userAgent;")

    def execute_script(self, script, arg=None):
        if arg is not None:
            self.driver.execute_script(script, arg)
        else:
            self.driver.execute_script(script)

    def switch_to_window(self, window_name):
        self.driver.switch_to.window(window_name)

    # def __del__(self):
    #     self.driver.quit()


# def referer(driver, ref_link, main_link):
#     """ get the main_link and make referer as ref_link """
#     import time
#     if '://' not in ref_link:
#         ref_links = [f'http://{ref_link}', f'https://{ref_link}']
#         LOG.info(
#             f'Reference link "{ref_link}" was given without http(s)://, so we tried to add prefix to it.')
#     else:
#         ref_links = [ref_link]
#     correct_ref_link = None
#     for ref_links in ref_links:
#         try:
#             load = driver.get(ref_link)
#             page_state = driver.execute_script('return document.readyState;')
#             print(page_state)
#             # print
#             # if not load:
#                 # return
#             correct_ref_link = ref_link
#         except selenium.common.exceptions.InvalidArgumentException:
#             continue
#     if correct_ref_link is not None:
#         driver.execute_script(f'window.location.href = "{main_link}";')
#     else:
#         LOG.info(
#             f'Reference link "{ref_link}" was incorrect. We wasn\'t able to complete it to the correct one.')
#         try:
#             driver.get(main_link)
#             page_state = driver.execute_script('return document.readyState;')
#             print(page_state)
#         except selenium.common.exceptions.InvalidArgumentException:
#             LOG.info('Incorrect site was given')
#             return False
#     return True


# def find_element_by_link(page_on_site, link):
#     """ test function """
#     session = requests.Session()
#     session.headers.update({
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15',
#         'Cookie': 'cycada=bPpdsL6OmVuA/vHwOkwEZ6b5m1yT1mYEBUWGwH8FGDg=; _ym_d=1576847554; _ym_uid=1570718328767985713; _ym_visorc_22663942=b; _ym_visorc_52332406=b; mda_exp_enabled=1; noflash=true; sso_status=sso.passport.yandex.ru:synchronized_no_beacon; tc=1; user_country=ru; yandex_gid=213; yandex_plus_metrika_cookie=true; PHPSESSID=jsb8usnpa8ovgsjtjp9gg10kk3; mobile=no; _csrf_csrf_token=uDZ_fZZywgrIXC2KLpV2V6G_K71VsmISBCwNr0heC4U; _ym_isad=2; _ym_wasSynced=%7B%22time%22%3A1576844395295%2C%22params%22%3A%7B%22eu%22%3A0%7D%2C%22bkParams%22%3A%7B%7D%7D; mda=0; desktop_session_key=139f10f99471995a1b48eecf0b98f5888c9219d00a10771efaba78cabc3dbaaeecd4f9dfd069f86f3ebf8f6b3a2bfb97bd95a5a3387a5bf37859968e4d756ffafaf00965312aa4f2cc93c262df127542eb204f0518e55383ed78b02c0dce7e36; desktop_session_key.sig=dP943b2vDA3HinOlIUvCc8FOVBs; user-geo-country-id=2; user-geo-region-id=213; lfiltr=all; i=q5DjteMdDtdbTPiy8XS1deq7n8vXuonLoQeLibMR86Zz/u+f0CVJZDEJHTndsyoTjK9LBCz3DwQ8WWr5hbXDZSmu60I=; mda2_beacon=1575744883269; ya_sess_id=3:1575744883.5.1.1568026663610:lXu8Lg:1d.1|924553428.-1.0.1:201533161|894704379.-1.0.1:191832246.2:1397019|30:185633.95409.RVP7okPx9W_5Mm-mpZ96xd48jxs; yandex_login=uid-ledkxpyj; yandexuid=5418682411560849018; my_perpages=%7B%2260%22%3A200%7D; _ym_d=1574701806; _ym_uid=1570718328767985713',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#         'Accept-Encoding': 'br, gzip, deflate',
#         'Accept-Language': 'ru'
#     })
#     page = session.get(page_on_site)
#     html = bs(page.text, 'html.parser')
#     href = html.find_all(href=link)
#     while link and not href:
#         link = '/'.join(link.split('/')[1:])
#         href = html.find_all(href=link)
#         href.extend(html.find_all(href='/' + link))
#     return href


# def get_location(obj, ret=False):
#     button = obj
#     size = button.size
#     if size['width'] or size['height'] == 0:
#         return -1, -1
#     print(f'size = {size}')
#     location = button.location
#     x = randint(-size['width'] + 1, size['width'] - 1)
#     y = randint(-size['height'] + 1, size['height'] - 1)
#     if ret:
#         return x, y
#     return location['x'] + x, location['y'] + y


# def send_search_request(texts):
#     lst = []
#     for text in texts:
#         lst.append(f'https://yandex.ru/search/?lr=213&text={urllib.parse.quote(text)}&noreask=1')
#         lst.append(f'https://www.google.com/search?q={text}&oq={text}')
#     return lst


# if __name__ == '__main__':
#     from scrolling import scroll
#     from chrome_driver import return_driver

#     # print(find_element_by_link('https://zonaofgames.ru/%d1%81%d0%b0%d0%b9%d1%82-%d0%b4%d0%bb%d1%8f-%d0%be%d0%b3%d1%80%d0%be%d0%bc%d0%bd%d0%be%d0%b3%d0%be-%d0%ba%d0%be%d0%bb%d0%b8%d1%87%d0%b5%d1%81%d1%82%d0%b2%d0%b0-%d0%b3%d0%b5%d0%b9%d0%bc%d0%b5%d1%80/%d0%b8%d0%b3%d1%80%d1%8b-%d0%ba%d0%bb%d1%8e%d1%87%d0%b8-%d0%bf%d0%b0%d1%82%d1%87%d0%b8/', 'https://zonaofgames.ru/%d1%81%d0%b0%d0%b9%d1%82-%d0%b4%d0%bb%d1%8f-%d0%be%d0%b3%d1%80%d0%be%d0%bc%d0%bd%d0%be%d0%b3%d0%be-%d0%ba%d0%be%d0%bb%d0%b8%d1%87%d0%b5%d1%81%d1%82%d0%b2%d0%b0-%d0%b3%d0%b5%d0%b9%d0%bc%d0%b5%d1%80/%d0%b8%d0%b3%d1%80%d1%8b-%d0%ba%d0%bb%d1%8e%d1%87%d0%b8-%d0%bf%d0%b0%d1%82%d1%87%d0%b8/#!digiseller/articles/96429'))
#     # print()
#     # print(find_element_by_link('https://zonaofgames.ru/%d1%81%d0%b0%d0%b9%d1%82-%d0%b4%d0%bb%d1%8f-%d0%be%d0%b3%d1%80%d0%be%d0%bc%d0%bd%d0%be%d0%b3%d0%be-%d0%ba%d0%be%d0%bb%d0%b8%d1%87%d0%b5%d1%81%d1%82%d0%b2%d0%b0-%d0%b3%d0%b5%d0%b9%d0%bc%d0%b5%d1%80/%d0%b8%d0%b3%d1%80%d1%8b-%d0%ba%d0%bb%d1%8e%d1%87%d0%b8-%d0%bf%d0%b0%d1%82%d1%87%d0%b8/', 'https://zonaofgames.ru/%d1%81%d0%b0%d0%b9%d1%82-%d0%b4%d0%bb%d1%8f-%d0%be%d0%b3%d1%80%d0%be%d0%bc%d0%bd%d0%be%d0%b3%d0%be-%d0%ba%d0%be%d0%bb%d0%b8%d1%87%d0%b5%d1%81%d1%82%d0%b2%d0%b0-%d0%b3%d0%b5%d0%b9%d0%bc%d0%b5%d1%80/%d0%b8%d0%b3%d1%80%d1%8b-%d0%ba%d0%bb%d1%8e%d1%87%d0%b8-%d0%bf%d0%b0%d1%82%d1%87%d0%b8/#!digiseller/detail/2640255'))
#     driver = return_driver(user_agent='ie')
#     referer(driver, 'https://yandex.ru/search/?lr=213&text=test&noreask=1',
#             'https://zonaofgames.ru/')
#     for i in range(50):
#         sleep(0.5)
#         scroll(driver, 10)
#     get(driver, 'https://im-a-good-boye.itch.io/blawk')
#     driver.quit()


def main():
    driver = Driver(proxy='https://179.61.188.91:45785')
    driver.get('https://www1.pinnacle.com/en/casino/games/live/roulette')
    proceed_link = driver.find_by_id("proceed-link")
    start = time.time()
    driver.implicitly_wait(5)
    end = time.time()
    print(f'time passed: {end - start}')
    if proceed_link is not None:
        proceed_link.click()
    sleep(100)


if __name__ == '__main__':
    main()
