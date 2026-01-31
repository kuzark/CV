'''Для обновления приложений на всех компьютерах использую публичный репозиторий на GitHub без кода приложения, приложение автоматически проверяет наличие свежей сборки в репозитории при запуске.'''

import requests
from tkinter.messagebox import showerror, showinfo
from webbrowser import open_new_tab
from app_data import (
    REPO_PUBLIC_NAME,
    CURRENT_VERSION,
)


class UpdateApp:
    '''Класс для проверки обновлениий приложения'''
    def __init__(self):

        # Ссылка на страницу с релизами
        self.releases_url = 'https://api.github.com/repos/'
        self.releases_url += f'kuzark/{REPO_PUBLIC_NAME}'
        self.releases_url += '/releases/latest'
        
        # Получение последней версии и ссылки на релиз
        self.latest_version, self.download_url = self._get_latest_version()

        # Проверка на совпадение версий
        self._check_update()

    
    def _get_latest_version(self):
        '''Получение последней версии'''
        try:
            # Попытка получения версии тега и ссылки на релиз
            response = requests.get(self.releases_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['tag_name'], data['assets'][0]['browser_download_url']
        except requests.RequestException as err:
            # При возникновении ошибки вывод окна с ошибкой
            err_msg = f'Ошибка! Код: {err}'
            showerror(title='Ошибка', message=err_msg)
            raise Exception

    
    def _check_update(self):
        '''Сравнивает версии, если полученная версия новее, 
        предлагает скачать по ссылке'''
        if self.latest_version != CURRENT_VERSION:

            # Вывод сообщения о новой версии
            msg = f'Доступна новая версия программы {self.latest_version}'
            msg += '\nСтраница для скачивания откроется автоматически после '
            msg += 'того, как закроете сообщение.'
            showinfo(title='Вышла новая версия', message=msg)

            # Открытие браузера со страницей для скачивания новой версии
            open_new_tab(self.download_url)
            
            # Вывод ошибки для выхода из приложения
            raise Exception
