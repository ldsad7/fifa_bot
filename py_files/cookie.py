import pickle


class Cookie:
    def __init__(self, driver, path):
        self.driver = driver
        self.path = path

    def save_cookie(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self.driver.get_cookies(), f)

    def load_cookie(self):
        with open(self.path, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
