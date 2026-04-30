'''Для обновления приложений на всех компьютерах использую публичный репозиторий на GitHub без кода приложения, приложение автоматически проверяет наличие свежей сборки в репозитории при запуске.'''

import requests
from tkinter.messagebox import showerror, showinfo
from tkinter.filedialog import askdirectory
from os import getenv
from pathlib import Path

# Мои модули
from app_data import CURRENT_VERSION, ERROR_MSG, INFO_MSG
from interface import ShowWaitingWindow


class UpdateApp:
    '''Класс для проверки обновлениий приложения'''
    def __init__(self):
        # Токен для авторизации на Яндекс Диске
        token = getenv('YA_DISK_TOKEN')
        # Заголовки запроса
        self.headers = {'Authorization': f'OAuth {token}'}
        # URL API Яндекс Диска
        self.API_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        # Начало процесса обновления
        self._start_update()

    
    def _request_execute(self, url, params='', stream=False):
        '''Выполнение запроса к API'''
        try:
            # Попытка получения результатов запроса
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                stream=stream, 
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.RequestException as err:
            # При возникновении ошибки вывод окна с ошибкой
            err_msg = f'Ошибка! Код: {err}'
            showerror(title=ERROR_MSG, message=err_msg)
            return
        

    @ShowWaitingWindow('Проверка наличия обновлений')
    def _get_last_version_data(self):
        '''Запрашивает имя и путь сборки последней загруженной сборки'''
        responce = self._request_execute(
            url=self.API_url,
            params={
                'path': 'app:/',
                'sort': '-created',
                'limit': 1,
                'fields': 'items.name,items.path'
            }
        )
        if responce: return responce.json()['_embedded']['items'][0]


    @ShowWaitingWindow('Получение ссылки для скачивания')
    def _get_download_link(self, file_path):
        '''Получение ссылки для скачивания'''
        responce = self._request_execute(
            url=f'{self.API_url}/download',
            params={
                'path': file_path,
                'fields': 'href'
            }
        )
        if responce: return responce.json()['href']
    

    @ShowWaitingWindow('Загрузка новой версии приложения', progress=True)
    def _download_update_file(self, download_link, save_path, progress_window):
        '''Выполняет загрузку новой сборки'''
        responce = self._request_execute(url=download_link, stream=True)
        total_size = int(responce.headers['content-length'])
        downloaded = 0
        try:
            with open(save_path, 'wb') as file:
                for chunk in responce.iter_content(chunk_size=8192):
                    file.write(chunk)
                    downloaded += len(chunk)
                    progress_window.set_progress(
                        (downloaded / total_size) * 100
                    )
        except requests.RequestException as err: 
            showerror(
                title=ERROR_MSG, message=f'Ошибка при загрузке: {repr(err)}'
            )
            # Удаление поврежденного файла, если есть
            self._clean_corrupted_file(save_path)
            return
        showinfo(title=INFO_MSG, message='Новая версия успешно загружена')
    

    def _clean_corrupted_file(self, save_path):
        '''Удаляет поврежденный (недокачанный) файл новой версии'''
        try: 
            if save_path.exists():
                save_path.unlink()
        except Exception as err:
            showerror(
                title=ERROR_MSG, 
                message=f'Не удалось удалить поврежденный файл: {repr(err)}'
            )


    def _start_update(self):
        '''Сравнивает версии, если полученная версия новее, 
        выполняет скачивание новой версии'''
        # Получение имени и пути последней загруженной версии
        data = self._get_last_version_data()
        if not data: raise Exception
        
        # Парсинг версии из имени файла сборки и сравнение версий
        latest_version = data['name'].split('-')[1].rsplit('.', 1)[0]
        if latest_version != CURRENT_VERSION:
            
            # Вывод сообщения о новой версии
            msg = f'Доступна новая версия программы {latest_version}. '
            msg += 'Далее будет загружена обновленная копия приложения.'
            showinfo(title='Вышла новая версия!', message=msg)

            # Запрос у пользователя пути для сохранения дополнения
            save_path = askdirectory(
                title='Выберите папку для сохранения приложения',
                mustexist=True
            )
            if not save_path: raise Exception
            # Добавление имени файла к ссылке
            save_path = Path(save_path) / data['name']

            # Получение ссылки для скачивания
            download_link = self._get_download_link(data['path'])
            if not download_link: raise Exception

            # Скачивание новой сборки
            self._download_update_file(download_link, save_path)
            
            # Вывод ошибки для выхода из приложения
            raise Exception
