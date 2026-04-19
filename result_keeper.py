'''Класс для загрузки CSV-файла, выгруженного непосредственно с анализатора крови, и преобразования в датафрейм'''

import pandas as pd
from tkinter.messagebox import showerror
from tkinter.filedialog import askopenfilename
import pdfplumber

# Мои модули
from app_data import ERROR_MSG


class ResultKeeper:
    '''Класс для хранения датафреймов с результатами анализов'''
    def __init__(self, app, load_title, encoding='utf-8', pdf=False):
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
        # Загрузка PDF
        self.pdf = pdf

    # Загрузка и получение датафрейма из файла с анализами
    @property
    def df(self):
        return self._df
    @df.setter
    def df(self, path):
        try:
            if self.pdf: self._df = self._df_from_pdf(path)
            else: self._df = pd.read_csv(path, encoding=self.encoding)
            self.loaded = True
        except Exception as err:
            self.app.logger.error(repr(err))
            showerror(
                title=ERROR_MSG,
                message='Ошибка загрузки файла. Проверьте лог.'
            )
    

    def _df_from_pdf(self, pdf_path):
        '''Датафрейм из PDF'''
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_tables = []
                # Получение из PDF всех таблиц со всех страниц
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        table_df = pd.DataFrame(table[1:], columns=table[0])
                        all_tables.append(table_df)
            # Объединение таблиц и форматирование столбцов Результат и Тест
            if all_tables: 
                joined_df = pd.concat(all_tables, ignore_index=True)
                joined_df['Результат'] = joined_df['Результат'].apply(
                    self._get_digit_result
                )
                joined_df['Тест'] = joined_df['Тест'].apply(
                    lambda s: s.replace('\n', ' ')
                )
                return joined_df
            else: raise Exception('PDF-файл не содержит таблиц')
        except Exception as err: 
            raise Exception(f'Ошибка при чтении PDF: {repr(err)}')
    

    def _get_digit_result(self, result):
        '''Оставляет в колонке "Результат" только значения'''
        digit_result_list = []
        # Отбор цифр и разделителя в виде точки или дефиза
        for symbol in result:
            if symbol.isdigit() or symbol in ('.', '-'):
                digit_result_list.append(symbol)
        
        # Если нет числового значения, то возвращается пустая строка
        if not digit_result_list: return ''
        result = ''.join(digit_result_list) # Формирование строки из списка
        # Если дефиз в значении возврат неизмененной строки
        if '-' in result: return result
        # Преобразование списка в строку и далее в число
        try: result = float(result)
        except Exception: return '' # Если не число, то возврат пустой строки
        if not result: return '' # Если 0, то возвращается пустая строка
        
        # Получение двух знаков после запятой
        first_digit = int(result * 10) % 10
        second_digit = int(result * 100) % 10
        # Если 3-й знак после запятой не равен 0 (уд.вес) возврат исх. значения
        if (int(result * 1000) % 10) != 0: return str(result)
        
        # Возвращение результата в виде строки
        # Возврат до 1 цифры после запятой, если второй знак 0
        if second_digit == 0 and first_digit != 0: return f'{result:.1f}'
        # Возврат до целого, если первый знак после запятой тоже 0
        elif first_digit == 0 and second_digit == 0: return f'{result:.0f}'
        else: return str(result)


def get_analysis_file_path(title, pdf=False):
    '''Возвращает путь к файлу с анализами'''
    defaultextension='.csv',
    filetypes=[('CSV-файл', '*.csv')]
    if pdf:
        defaultextension='.pdf',
        filetypes=[('PDF-файл', '*.pdf')]
    return askopenfilename(
        title=title,
        defaultextension=defaultextension,
        filetypes=filetypes,
    )
