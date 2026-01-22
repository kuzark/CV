from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment, Font
from tkinter.messagebox import showerror, showinfo
from tkinter.filedialog import asksaveasfilename
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Мои модули
from app_data import (
    ERROR_MSG, 
    DATE_FORMAT_FULL_YEAR,
    DATE_TIME_FORMAT,
    INFO_MSG,
)
from .models import Patient


class ReportMaker:
    '''Создание отчета по дневному стационару в excel'''

    def __init__(self, app):

        # Загрузка шаблона
        self.wbook = load_workbook(app.tmp_paths.templates / 'report.xlsx')
        self.wsheet = self.wbook.active

        # Границы для ячеек
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        )
        
        # Шрифт и выравнивание текста в ячейках
        self.font = Font(name='Times New Roman', size=11)
        self.alignment = Alignment(
            horizontal='center', vertical='center', wrap_text=True
        )

        # Создание класса сессии подключения к БД
        self.Session = sessionmaker(autoflush=False, bind=app.engine)

        # Доступ к логгеру
        self.logger = app.logger

        # Строка с текущими датой и временем
        now = datetime.now()
        self.time_str = now.strftime(DATE_TIME_FORMAT)
        
        # Создание отчета
        success = self._fill_table()
        if success: # Если функция прошла успешно
            self._save_excel_file()
        

    def _get_all_patients_db(self):
        '''Загружаем всех пациентов из базы данных'''
        try:
            with self.Session() as db:
                patients = db.query(Patient).all()
        except Exception as err:
            self.logger.error(f'Ошибка чтения из БД: {err}')
            showerror(
                title=ERROR_MSG,
                message='Ошибка чтения из БД. Смотрите лог'
            )
            return 'error'
        else: return patients

    
    def _fill_table(self):
        '''Заполнение таблицы'''
        # Загрузка пациентов из БД
        patients = self._get_all_patients_db()
        # Проверки на ошибки или пустой БД
        if patients == 'error': return False
        if not patients: 
            showinfo(title=INFO_MSG, message='Нет пациентов в базе')
            return False
        
        # Словарь функций для заполнения строки пациента
        fill_funcs = {
            'A': lambda: i + 1,
            'B':
            lambda: f'{patient.surname} {patient.name} {patient.patronymic}',
            'C': lambda: patient.birth_date.strftime(DATE_FORMAT_FULL_YEAR),
            'D': lambda: self._get_dates_hospital_string(patient, 1),
            'E': lambda: self._get_dates_hospital_string(patient, 2),
            'F': lambda: self._get_dates_hospital_string(patient, 3),
            'G': lambda: patient.doctor,
            'H': lambda: patient.treatment,
        }
        
        # Заполнение и форматирование ячеек
        for i, patient in enumerate(patients):
            row = i + 2
            for letter, func in fill_funcs.items():
                self.wsheet[f'{letter}{row}'] = func()
                self.wsheet[f'{letter}{row}'].border = self.border
                self.wsheet[f'{letter}{row}'].font = self.font
                self.wsheet[f'{letter}{row}'].alignment = self.alignment
        return True # Успешное выполнение функции
  
        
    def _get_dates_hospital_string(self, patient, num):
        '''Возвращает строку с датами госпитализации'''
        # Получение атрибутов
        dates = [
            getattr(patient, f'start_{num}_hospitalization'),
            getattr(patient, f'end_{num}_hospitalization')
        ]
        
        # Перевод даты в строку
        for i in range(len(dates)):
            # Если атрибут пустой выход из функции
            if not dates[i]:
                return
            dates[i] = dates[i].strftime(DATE_FORMAT_FULL_YEAR)
        
        return f'{dates[0]} - {dates[1]}'

    
    def _save_excel_file(self):
        '''Сохраняет файл в указанное место'''
        path = asksaveasfilename(
            initialfile=f'Отчет от {self.time_str}',
            defaultextension='.xlsx'
        )
        if path:
            self.wbook.save(path)