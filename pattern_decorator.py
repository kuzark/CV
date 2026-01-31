from tkinter import ttk

# Мои модули
from .base_window import BaseFormWindow


class WaitingWindow(BaseFormWindow):
    '''Окно ожидания завершения операции'''
    def __init__(self, process_name):
        super().__init__('Ожидайте...')
        self.protocol('WM_DELETE_WINDOW', lambda: None) # Блокировка крестика
        
        # Виджеты окна
        frame = ttk.Frame(self, relief='sunken')
        ttk.Label(frame, text=process_name).grid(padx=20, pady=20)
        frame.grid(padx=2, pady=2)

        # Расположение окна по центру экрана
        self.update_idletasks()
        self.geometry(self.align_center_screen(self.geometry()))


class ShowWaitingWindow:
    '''Декоратор для показа окна ожидания'''
    def __init__(self, process_name):
        self.process_name = process_name
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            window = WaitingWindow(self.process_name)
            # Принудительная отрисовка окна
            window.update()
            result = [] # Список для хранения результата декорируемой функции
            def run():
                result.append(func(*args, **kwargs))
                window.dismiss() # Закрытие окна
            window.after(500, run) # Запуск функции с задержкой для отрисовки
            window.wait_window(window) # Блок управления до завершения операций
            return result[0]
        return wrapper

'''Использование декоратора в коде'''
def _check_updates(self):
    '''Проверка обновлений'''
    @ShowWaitingWindow('Проверка наличия обновлений...')
    def update_app():
        try:
            UpdateApp()
            return True
        except Exception:
            return False
        
