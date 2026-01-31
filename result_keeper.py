'''Класс для загрузки CSV-файла, выгруженного непосредственно с анализатора крови, и преобразования в датафрейм'''

import pandas as pd
from tkinter.messagebox import showerror
from tkinter.filedialog import askopenfilename

# Мои модули
from app_data import ERROR_MSG


class ResultKeeper:
    '''Класс для хранения датафреймов с результатами анализов'''
    def __init__(self, app, load_title, encoding='utf-8'):
        # Экземпляр приложения
        self.app = app
        # Заголовок для окна загрузки
        self.load_title = load_title
        # Кодировка файла
        self.encoding = encoding
        # Переменная для хранения датафрейма с анализами
        self._df = None
        # Флаг загрузки файла с анализами
        self.loaded = False

    # Загрузка и получение датафрейма из файла с анализами
    @property
    def df(self):
        return self._df
    @df.setter
    def df(self, path):
        try:
            self._df = pd.read_csv(path, encoding=self.encoding)
            self.loaded = True
        except Exception as err:
            self.app.logger.error(err)
            showerror(
                title=ERROR_MSG,
                message='Ошибка загрузки файла. Проверьте лог.'
            )


def get_analysis_file_path(title):
    '''Возвращает путь к файлу с анализами'''
    return askopenfilename(
        title=title,
        defaultextension='.csv',
        filetypes=[('CSV-файл', '*.csv')],
    )
