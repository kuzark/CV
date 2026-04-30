'''Классы для работы с базой данных'''

from abc import ABC, abstractmethod
from tkinter.messagebox import showerror, showwarning

# Мои модули
from app_data import ERROR_MSG, WARNING_MSG


class DataBaseHandler(ABC):
    '''Базовый класс для работы с базой данных.
    Вызывается через call_method(app, method)'''
    @classmethod
    def call_method(cls, app, method):
        '''Проверяет создан ли экземпляр и выполняет метод'''
        instance = cls(app)
        if instance:
            instance._methods[method]()
            return instance
        
    
    def __new__(cls, app):
        '''Проверяет наличие атрибута patient у главного приложения
        и только, если есть атрибут создает экземпляр класса'''
        if hasattr(app, 'patient'): return super().__new__(cls)
        return None
    
    
    def __init__(self, app):
        # Доступ к экземпляру приложения
        self._app = app
        # Доступ к логгеру
        self._logger = app.logger
    

    @property
    @abstractmethod
    def _methods(self):
        '''Обязательно определить словарь с методами для каждого класса'''
        pass
    

    @property
    @abstractmethod
    def _db_cls(self):
        '''Обязательно определить класс БД'''
        pass


    @property
    @abstractmethod
    def _session(self):
        '''Обязательно определить сессию'''
        pass

    
    def _find_patient(self):
        '''Поиск пациента в базе'''
        try:
            with self._session() as db:
                patients = db.query(self._db_cls).filter(
                    self._db_cls.surname == self._app.patient.surname
                ).filter(
                    self._db_cls.name == self._app.patient.name
                ).filter(
                    self._db_cls.patronymic == self._app.patient.patronymic
                ).filter(
                    self._db_cls.birth_date == self._app.patient.birth_date
                ).all()
        except Exception as err:
            self._logger.error(f'Ошибка поиска в БД: {repr(err)}')
            showerror(
                title=ERROR_MSG,
                message='Ошибка поиска в БД. Смотрите лог'
            )
            return 'error'
        else: return patients

    
    def _check_correct_finding(self, patients):
        '''Проверяет корректность результатов поиска'''
        # Ошибка при поиске
        if patients == 'error':
            self._clear_patient_data()
            return
        # Пациент не найден
        elif not patients:
            self._clear_patient_data()
            self._logger.warning('Пациент не найден')
            showwarning(title=WARNING_MSG, message='Пациент не найден')
            return
        # Найдено более одного пациента
        elif len(patients) > 1:
            err_msg = 'Найдено более одного пациента. Проверьте базу данных'
            self._logger.error(err_msg)
            self._clear_patient_data()
            showerror(title=ERROR_MSG, message=err_msg)
            return
        # Найден один пациент
        else: return True

    
    def _clear_patient_data(self):
        '''Удаляет переменную пациента с неактуальными поисковыми данными
        и логирует'''
        attr_name = self._clear_data()
        self._logger.info(f'Очищен локальный атрибут пациента: {attr_name}')


    @abstractmethod
    def _clear_data(self):
        '''Определить какой атрибут удаляется и необходимо ли очишения
        строки пациента на главном окне'''
        pass


    def _error_log_rollback(self, db, err, msg):
        '''Сообщает об ошибке и записывает в лог, откатывает базу данных'''
        db.rollback()
        self._logger.error(f'{msg}: {repr(err)}')
        showerror(title=ERROR_MSG, message=f'{msg}. Смотрите лог')


from sqlalchemy.orm import sessionmaker
from tkinter.messagebox import showinfo, askyesno

# Мои модули
from app_data import WARNING_MSG, INFO_MSG, NO_PATIENT
from ..models import PatientDH
from ..log_handler import log_patient_attrs
from .base import DataBaseHandler


class DayHospitalHandlerDB(DataBaseHandler):
    '''Класс для работы с БД дневного стационара'''
    @property
    def _methods(self):
        '''Используемые методы в классе'''
        return {
            'create': self._create,
            'load': self._load_patient,
        }
    
    @property
    def _db_cls(self):
        '''Класс используемой БД'''
        return PatientDH

    @property
    def _session(self):
        '''Сессия для подключения к БД'''
        return sessionmaker(autoflush=False, bind=self._app.dh_engine)
    

    def __init__(self, app):
        super().__init__(app)
        # Доступ к переменной кнопки и надписи пациента на главном окне
        self.patient_label = app.patient_label
        self.patient_button = app.patient_button


    def _create(self):
        '''Добавление нового пациента в базу данных или перезапись'''
        # Существует ли уже пациент в базе данных? (поиск)
        patients = self._find_patient()
        # Останавливает функции при ошибке в функции поиска пациента
        if patients == 'error':
            return
        # Если такой пациент найден, запрос о перезаписи
        elif patients:
            if askyesno(
                title=WARNING_MSG, 
                message='Пациент уже есть в базе.',
                detail='Обновить его данные?'
            ):
                # Обновление пациента в базе данных
                self._update_patient_db(patients[0])
            else: return
        # Если не найден, добавление пациента в базу данных
        else: self._add_patient_to_db()

    
    def _update_patient_db(self, finded_patient):
        '''Обновляет данные пациента в базе данных'''
        # Присваивание id найденного пациента локальной версии
        self._app.patient.id = finded_patient.id
        # Обновление данных
        with self._session() as db:
            try:
                saved_patient = db.merge(self._app.patient)
                db.commit()
                db.refresh(saved_patient)
                self._app.patient = saved_patient
            except Exception as err:
                msg = 'Ошибка обновления данных в БД'
                self._error_log_rollback(db, err, msg)
            else: 
                showinfo(title=INFO_MSG, message='Данные пациента обновлены')
                # Блокировка кнопки пациента
                self.patient_button.config(state='disabled')

    
    def _add_patient_to_db(self):
        '''Добавляет пациента в базу данных'''
        with self._session() as db:
            try:
                db.add(self._app.patient)
                db.commit()
                db.refresh(self._app.patient)
            except Exception as err:
                msg = 'Ошибка записи в БД'
                self._error_log_rollback(db, err, msg)
            else: 
                showinfo(title=INFO_MSG, message='Пациент успешно добавлен')
                # Блокировка кнопки пациента
                self.patient_button.config(state='disabled')

    
    def _load_patient(self):
        '''Присвоение глобальной переменной атрибутов найденного пациента'''
        # Поиск и проверка корректности результатов
        patients = self._find_patient()
        if self._check_correct_finding(patients):
            # Присвоение найденного пациента глобальной переменной пациента
            self._app.patient = patients[0]

            # Смена текста надписи пациента на главном экране на текущего
            text = (
                f'{self._app.patient.surname} {self._app.patient.name} '
                f'{self._app.patient.patronymic} '
                f'{self._app.patient.birth_date.strftime("%d.%m.%Y")}'
            )
            self.patient_label.set(text)

            # Внесение в лог
            self._logger.info('Загружен пациент из базы данных.')
            log_patient_attrs(
                self._app.patient,
                self._logger,
                self._app.patient.all_attrs
            )

    
    def _clear_data(self):
        '''Очищает атрибут и строку пациента на главном окне'''
        self.patient_label.set(NO_PATIENT)
        delattr(self._app, 'patient')
        return 'patient'
    
from sqlalchemy.orm import sessionmaker
from tkinter.messagebox import showinfo

# Мои модули
from app_data import INFO_MSG
from .base import DataBaseHandler
from ..models import PatientWL


class WaitingListHandlerDB(DataBaseHandler):
    '''Класс для работы с БД листа ожидания'''
    @property
    def _methods(self):
        '''Используемые методы в классе'''
        return {
            'update': self._update_patient,
            'load': self._load_patient,
        }

    @property
    def _db_cls(self):
        '''Класс используемой БД'''
        return PatientWL

    @property
    def _session(self):
        '''Сессия для подключения к БД'''
        return sessionmaker(autoflush=False, bind=self._app.wl_engine)
    

    def __init__(self, app):
        super().__init__(app)
        # Флаг при успешном поиске пациента
        self.success_finding = False
    

    def _clear_data(self):
        '''Очищает атрибут пациента'''
        delattr(self._app, 'patient_wl')
        return 'patient_wl'
    

    def _load_patient(self):
        '''Присвоение глобальной переменной атрибутов найденного пациента'''
        # Поиск и проверка корректности результатов
        patients = self._find_patient()
        if self._check_correct_finding(patients):
            # Присвоение найденного пациента в переменную ЛС
            self._app.patient_wl = patients[0]
            self.success_finding = True

    
    def _update_patient(self):
        '''Обновляет данные пациента в Листе ожидания'''
        with self._session() as db:
            try:
                result = db.query(self._db_cls).filter_by(
                    id=self._app.patient_wl.id
                ).update(
                    {
                        'is_treating': True,
                        'budget': 'ОМС',
                        'scheme': self._app.patient.treatment,
                    }
                )
                db.commit()
                # Если пациент по id не найден (обновлено 0 строк) 
                # выбрасывается исключение
                if not result: raise ValueError('ID не найден')
            except Exception as err:
                self._clear_patient_data()
                msg = 'Ошибка обновления данных в Листе ожидания'
                self._error_log_rollback(db, err, msg)
            else:
                self._logger.info(
                    f'Данные пациента (ID: {self._app.patient_wl.id}) успешно '
                    'обновлены в Листе ожидания. Статус: взят на лечение, '
                    'бюджет - ОМС, схема лечения - '
                    f'{self._app.patient.treatment}'
                )
                self._clear_patient_data()
                showinfo(
                    title=INFO_MSG, message='Лист ожидания успешно обновлен'
                )