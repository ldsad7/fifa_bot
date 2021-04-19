import threading

import PySimpleGUI as sg

from browser import Browser

WINDOW_SIZE = (1280, 480)
EXIT = 'Выйти'
LAUNCH = 'Запустить бота'


def run_interface():
    layout = [
        [sg.Text('○ Настройки FIFA бота', background_color='black', text_color='white',
                 justification='center', size=(WINDOW_SIZE[0], 1))],
        [sg.Text('Границы времени для ставки (левая и правая граница входят)'),
         sg.Spin(values=[i for i in range(1, 200)], initial_value=0, key='left_border'),
         sg.Spin(values=[i for i in range(1, 200)], initial_value=85, key='right_border')],
        [sg.Text('Коэффициент, при достижении которого делается ставка'),
         sg.Spin(values=[i for i in range(50)], initial_value=1, key='coef')],
        [sg.Text('Размер начальной ставки (в валюте пользователя)'),
         sg.Spin(values=[i for i in range(1000)], initial_value=1, key='first_bet')],
        [sg.Text('Последовательность, отвечающая за увеличение ставки при проигрыше (нужно вводить послед-ть через пробел):')],
        [sg.Radio('Последовательность Фибоначчи', group_id='RADIO1', default=True, key='fibonacci_seq'),
         sg.Radio('Своя последовательность:', group_id='RADIO1', key='custom_seq_radio_button'),
         sg.InputText(key='custom_seq')],
        [sg.Button(LAUNCH), sg.Button(EXIT)]
    ]

    window = sg.Window("FIFA бот", layout, size=WINDOW_SIZE)

    was_exit = False
    while True:
        event, values = window.read(timeout=1000)
        if event == sg.WIN_CLOSED or event == EXIT:
            was_exit = True
            break
        elif event == LAUNCH:
            values['proxy'] = None
            break

    # SETTING VARS
    if not was_exit:
        browser: Browser = Browser(**values)
        t = threading.Thread(target=browser.run_program, args=(), kwargs={}, daemon=True)
        t.start()
        while True:
            event, values = window.read(timeout=1000)
            if event == sg.WIN_CLOSED or event == EXIT:
                break
    window.close()


def main():
    run_interface()


if __name__ == '__main__':
    main()
