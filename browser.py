import time
from dataclasses import dataclass
from functools import partial
from typing import Generator, Dict, Optional

from selenium.common.exceptions import StaleElementReferenceException

from local_settings import CREDENTIALS
from py_files.chrome_driver import Driver

RULE_BREAKS = [
    'Максимальное отклонение от значения Max', 'Максимальное количество неудачных предсказаний', 'Нет'
]
BREAK_RULES = ('Максимальное количество неудачных предсказаний', 'Нет')
CHIPS = ['0.20', '0.50', '1', '5', '25', '100']


class Iframe:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        """ ENTERING IFRAMES """
        self.driver.wait_until('[id="iFrameResizer0"]')
        iframes = [self.driver.driver.find_elements_by_tag_name('iframe[id="iFrameResizer0"]')]
        self.driver.driver.switch_to.frame(iframes[-1][-1])

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.driver.switch_to.default_content()  # switch back to the main window


class ReverseIframe:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        self.driver.driver.switch_to.default_content()  # switch back to the main window

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ ENTERING IFRAMES """
        self.driver.wait_until('[id="iFrameResizer0"]')
        iframes = [self.driver.driver.find_elements_by_tag_name('iframe[id="iFrameResizer0"]')]
        self.driver.driver.switch_to.frame(iframes[-1][-1])


def fibonacci_gen():
    first, second = 0, 1
    while True:
        next_num = first + second
        yield next_num
        first, second = second, next_num


def custom_gen(seq):
    try:
        seq = list(map(float, map(lambda s: s.replace(',', '.'), seq.split())))
    except Exception:
        raise ValueError("В заданной последовательности есть некорректные значения")
    for elem in seq:
        yield float(elem)
    while True:
        if not seq:
            yield 1
        else:
            yield seq[-1]


@dataclass
class Match:
    was_bet: bool  # была ставка или нет
    num_of_goals: Optional[int]  # какое было суммарное количество голов
    bet_generator: Generator[float, None, None]  # генератор последовательности ставок
    match_ended: bool  # закончился ли матч, т.е. нужно ли можно продолжать последовательность, заданную данным генератором


class Browser:
    def __init__(self, driver=None, **kwargs):
        if driver is None:
            self.driver = Driver(**kwargs)
        else:
            self.driver = driver
        self.driver.get(CREDENTIALS['site'])
        self.login()
        while self.driver.driver.current_url != CREDENTIALS['site']:
            driver.get(CREDENTIALS['site'])
        self.left_border = float(kwargs.get('left_border'))
        self.right_border = float(kwargs.get('right_border'))
        self.coef = float(kwargs.get('coef'))
        self.first_bet = float(kwargs.get('first_bet'))
        if kwargs.get('fibonacci_seq'):
            self.gen = partial(fibonacci_gen)
        else:
            self.gen = partial(custom_gen, kwargs.get('custom_seq'))

    @staticmethod
    def sleep(quantity):
        time.sleep(quantity)

    def login(self):
        login_check = self.driver.find_elements_by_css_selector(
            CREDENTIALS['login_check']
        )
        if not login_check:
            login_buttons = self.driver.find_elements_by_css_selector(
                CREDENTIALS['login_button']
            )
            if login_buttons:
                login_buttons[0].click()
            while login_buttons:
                time.sleep(8)
                login_buttons = self.driver.find_elements_by_css_selector(
                    CREDENTIALS['login_button']
                )
        self.driver.cookie.save_cookie()

    def try_in_cycle(self, code, button, locals_, globals_):
        while True:
            try:
                result = exec(code, locals_, globals_)
                break
            except Exception as e:
                print(e)
                print(f"Не смогли нажать на кнопку \"{button}\". Пробуем ещё раз")
        return result

    def close_header(self) -> None:
        self.driver.wait_until('[data-editor-id="betslipQuickBetHeader"]')
        self.driver.wait_until('[data-editor-id="betslipContent"]')
        # При нажатии на header меняется количество классов, больше ничего, названия классов предсказать затруднительно
        if len(self.driver.find_element_by_css_selector('[data-editor-id="betslipContent"]').get_attribute(
                'class').split()) != 5:
            self.try_in_cycle(
                "self.driver.find_element_by_css_selector('[data-editor-id=\"betslipQuickBetHeader\"]').click()",
                '[data-editor-id="betslipQuickBetHeader"]', locals(), globals()
            )

    def open_header(self) -> None:
        self.driver.wait_until('[data-editor-id="betslipQuickBetHeader"]')
        self.driver.wait_until('[data-editor-id="betslipContent"]')
        # При нажатии на header меняется количество классов, больше ничего, названия классов предсказать затруднительно
        if len(self.driver.find_element_by_css_selector('[data-editor-id="betslipContent"]').get_attribute(
                'class').split()) == 5:
            self.try_in_cycle(
                "self.driver.find_element_by_css_selector('[data-editor-id=\"betslipQuickBetHeader\"]').click()",
                '[data-editor-id="betslipQuickBetHeader"]', locals(), globals()
            )

    def run_program(self):
        self.try_in_cycle(
            "balance = self.driver.find_element_by_css_selector('.balance-menu__value>span').text",
            ".balance-menu__value>span", locals(), globals()
        )
        print(f'balance: {balance}')
        self.driver.wait_until('[data-editor-id="quickBetSwitcherButton"]')
        if self.driver.driver.find_elements_by_css_selector(
                '[data-editor-id="betslipHeader"] [data-editor-id="quickBetSwitcherButton"]'):
            self.try_in_cycle(
                "self.driver.driver.find_element_by_css_selector('[data-editor-id=\"quickBetSwitcherButton\"]').click()",
                '[data-editor-id="quickBetSwitcherButton"]', locals(), globals()
            )
        self.close_header()
        shadow_root = self.driver.expand_shadow_element(
            self.driver.driver.find_element_by_css_selector('#bt-inner-page')
        )
        self.try_in_cycle(
            "shadow_root.find_element_by_css_selector('[data-editor-id=\"pillTabs\"]:nth-child(2) div:nth-child(2)').click()",
            '[data-editor-id="pillTabs"]:nth-child(2) div:nth-child(2)', locals(), globals()
        )  # xpath doesn't work in shadow roots...
        self.try_in_cycle(
            "block_title = shadow_root.find_element_by_css_selector('[data-editor-id=\"blockTitle\"]');"
            "self.driver.execute_script('arguments[0].scrollIntoView();', block_title)",
            '[data-editor-id="blockTitle"]', locals(), globals()
        )

        matches: Dict[str, Match] = {}
        while True:
            self.try_in_cycle(
                "event_cards = shadow_root.find_elements_by_css_selector('[data-editor-id=\"eventCard\"]')",
                '[data-editor-id="eventCard"]', locals(), globals()
            )
            print(f'event_cards: {len(event_cards)}')
            for event_card in event_cards:
                self.try_in_cycle(
                    "title_elem, content, bets = event_card.find_elements_by_css_selector('[data-editor-id=\"eventCard\"] > div')",
                    '[data-editor-id="eventCard"]', locals(), globals()
                )
                title = title_elem.text
                print(f'NOW title: {title}')
                if title not in matches:
                    was_break = False
                    for key, match in matches.items():
                        if match.match_ended:
                            matches[title] = Match(
                                was_bet=False,
                                num_of_goals=None,
                                bet_generator=match.bet_generator,
                                match_ended=False
                            )
                            del matches[key]
                            was_break = True
                            break
                    if not was_break:
                        matches[title] = Match(
                            was_bet=False,
                            num_of_goals=None,
                            bet_generator=self.gen(),
                            match_ended=False
                        )
                print(f'matches[title]: {matches[title]}')
                minute, country_1, country_2, score_1, score_2 = content.text.split('\n')
                score_1, score_2 = list(map(int, [score_1, score_2]))
                if minute in ['Начался']:
                    if matches[title].match_ended:
                        matches[title] = Match(
                            was_bet=False,
                            num_of_goals=None,
                            bet_generator=matches[title].bet_generator,
                            match_ended=False
                        )
                    continue
                elif minute in ['Закончен']:
                    matches[title].match_ended = True
                    if matches[title].was_bet and score_1 + score_2 > matches[title].num_of_goals:
                        matches[title].bet_generator = self.gen()
                    continue
                elif '′' not in minute:
                    continue
                else:
                    minute = float(minute.split('′')[0])
                if minute < self.left_border or minute > self.right_border:
                    continue
                if bets.text == 'Нет доступных маркетов':
                    continue
                self.try_in_cycle(
                    "event_card.find_element_by_css_selector("
                    "'[data-editor-id=\"eventCard\"] > div:nth-child(3) > div:nth-child(2)').click()",
                    '[data-editor-id="eventCard"] > div:nth-child(3) > div:nth-child(2)', locals(), globals()
                )

                self.try_in_cycle(
                    "total = event_card.find_element_by_css_selector("
                    "'[data-editor-id=\"eventCardExtended\"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)'"
                    "); print(total.text) if total.text != '' else 1 / 0",
                    '[data-editor-id="eventCardExtended"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)',
                    locals(), globals()
                )
                bet_title, bet_value = total.text.split('\n')[:2]
                try:
                    bet_value = float(bet_value)
                except ValueError:
                    print("Не смогли посчитать значение для Тотала. Посчитаем в следующий раз")
                    continue

                if bet_value >= self.coef:
                    make_bet = False
                    if not matches[title].was_bet:
                        matches[title].was_bet = True
                        matches[title].num_of_goals = score_1 + score_2
                        make_bet = True
                    elif score_1 + score_2 > matches[title].num_of_goals:
                        matches[title].num_of_goals = score_1 + score_2
                        matches[title].bet_generator = self.gen()
                        make_bet = True
                    if make_bet:
                        self.open_header()
                        bet_value = next(matches[title].bet_generator) * self.first_bet
                        self.driver.wait_until('[data-editor-id="betslipStakeInput"] input')
                        self.try_in_cycle(
                            "bet_input = self.driver.driver.find_element_by_css_selector('[data-editor-id=\"betslipStakeInput\"] input')",
                            '[data-editor-id="betslipStakeInput"] input', locals(), globals()
                        )
                        while bet_input.get_attribute('value').strip() != str(bet_value):
                            print(f"input value: {bet_input.get_attribute('value').strip()}")
                            bet_input.clear()
                            bet_input.send_keys(str(bet_value))
                            self.try_in_cycle(
                                "bet_input = self.driver.driver.find_element_by_css_selector('[data-editor-id=\"betslipStakeInput\"] input')",
                                '[data-editor-id="betslipStakeInput"] input', locals(), globals()
                            )
                        self.try_in_cycle(
                            "elems = self.driver.driver.find_elements_by_xpath('//button[text()=\"Применить\"]');"
                            "elems[0].click() if elems else print('pass')",
                            "//button[text()='Применить']", locals(), globals()
                        )
                        self.close_header()

                        self.try_in_cycle(
                            "event_card.find_element_by_css_selector("
                            "'[data-editor-id=\"eventCardExtended\"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)'"
                            ").click()",
                            '[data-editor-id="eventCardExtended"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)',
                            locals(), globals()
                        )
                        self.close_header()
                self.try_in_cycle(
                    "event_card.find_element_by_css_selector("
                    "'[data-editor-id=\"eventCardExtended\"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(1)'"
                    ").click()",
                    '[data-editor-id="eventCardExtended"] > div:nth-child(3) > div:nth-child(2) > div:nth-child(1)',
                    locals(), globals()
                )


def main():
    browser = Browser(site='pinnacle')
    browser.run_program()


if __name__ == "__main__":
    main()
