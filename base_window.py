'''Базовый класс для создания окон для форм'''

from tkinter import Toplevel
import re

# Мои модули
from app_data import MARGINS


class BaseFormWindow(Toplevel):
    '''Базовое окно для форм'''
    @staticmethod
    def align_center_screen(geometry):
        '''Выравнивает окно по центру экрана'''
        # Поиск размеров окна в получаемой строке
        pattern = r'(\d+)x(\d+)'
        match = re.search(pattern, geometry)
        if match:
            sizes = match.groups()
        else: raise ValueError('Неверный формат размеров окна.')

        # Расчет отступов от границ экрана и возврат строки размеров окна
        x, y = map(int, sizes)
        x_margin = round((1920 - x) / 2)
        y_margin = round((1080 - y) / 2)
        return f'{x}x{y}+{x_margin}+{y_margin}'


    def __init__(self, title, geometry=None):
        super().__init__()

        # Настройки окна
        self.title(title) # Заголовок окна
        if geometry:
            self.geometry(self.align_center_screen(geometry)) # Размер окна
        self.resizable(False, False) # Отключение возможности менять размер окна
        self.protocol('WM_DELETE_WINDOW', self.dismiss) # При закрытии окна
        self.grab_set() # Пользовательский захват

        # Отступы
        self.margins = MARGINS

    
    def dismiss(self):
        '''Отключение пользовательского захвата при закрытии окна'''
        self.grab_release()
        self.destroy()
