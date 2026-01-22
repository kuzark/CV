from tkinter.messagebox import showerror, showinfo, askyesno
from sqlalchemy.orm import sessionmaker

# Мои модули
from app_data import ERROR_MSG, WARNING_MSG, INFO_MSG, NO_PATIENT
from .models import Patient
from .log_handler import log_patient_attrs

class CRUDcompleter:
    '''Выполняет CRUD действия с базой данных
    Вызывается через call_method(app, method)'''
    @staticmethod
    def call_method(app, method):
        '''Проверяет создан ли экземпляр и выполняет метод'''
        instance = CRUDcompleter(app)
        if instance:
            instance.methods[method]()
    
    
    def __new__(cls, app):
        '''Проверяет наличие атрибута patient у главного приложения
        и только, если есть атрибут создает экземпляр класса'''
        # Создает экземпляр
        instance = super().__new__(cls)
        
        # Проверяет наличие атрибута patient у главного приложения
        # Если нет возвращает None
        if not hasattr(app, 'patient'):
            return None
        
        return instance

    
    def __init__(self, app):
        # Словарь методов
        self.methods = {
            'create': self._create,
            'load': self._load_patient,
        }
        
        # Доступ к экземпляру приложения
        self.app = app

        # Доступ к движку базы данных
        self.engine = app.engine

        # Доступ к логгеру
        self.logger = app.logger

        # Доступ к переменной надписи пациента на главном окне
        self.patient_label = app.patient_label
        
        # Создание класса сессии
        self.Session = sessionmaker(autoflush=False, bind=self.engine)
    
    
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
    

    def _add_patient_to_db(self):
        '''Добавляет пациента в базу данных'''
        with self.Session() as db:
            try:
                db.add(self.app.patient)
                db.commit()
                db.refresh(self.app.patient)
            except Exception as err:
                msg = 'Ошибка записи в БД'
                self._error_log_rollback(db, err, msg)
            else: showinfo(title=INFO_MSG, message='Пациент успешно добавлен')
    

    def _update_patient_db(self, finded_patient):
        '''Обновляет данные пациента в базе данных'''
        # Присваивание id найденного пациента локальной версии
        self.app.patient.id = finded_patient.id
        # Обновление данных
        with self.Session() as db:
            try:
                saved_patient = db.merge(self.app.patient)
                db.commit()
                db.refresh(saved_patient)
                self.app.patient = saved_patient
            except Exception as err:
                msg = 'Ошибка обновления данных в БД'
                self._error_log_rollback(db, err, msg)
            else: showinfo(title=INFO_MSG, message='Данные пациента обновлены')
    

    def _error_log_rollback(self, db, err, msg):
        '''Сообщает об ошибке и записывает в лог, откатывает базу данных'''
        db.rollback()
        self.logger.error(f'{msg}: {err}')
        showerror(title=ERROR_MSG, message=f'{msg}. Смотрите лог')


    def _find_patient(self):
        '''Поиск пациента в базе'''
        try:
            with self.Session() as db:
                patients = db.query(Patient).filter(
                    Patient.surname == self.app.patient.surname
                ).filter(
                    Patient.name == self.app.patient.name
                ).filter(
                    Patient.patronymic == self.app.patient.patronymic
                ).filter(
                    Patient.birth_date == self.app.patient.birth_date
                ).all()
        except Exception as err:
            self.logger.error(f'Ошибка поиска в БД: {err}')
            showerror(
                title=ERROR_MSG,
                message='Ошибка поиска в БД. Смотрите лог'
            )
            return 'error'
        else: return patients
    

    def _load_patient(self):
        '''Присвоение глобальной переменной атрибутов найденного пациента'''
        patients = self._find_patient()
        # Возврат из функции 
        if patients == 'error':
            self._clear_search_data()
        elif not patients:
            self._clear_search_data()
            showinfo(title=INFO_MSG, message='Пациент не найден')
        elif len(patients) > 1:
            err_msg = 'Найдено более одного пациента. Проверьте базу данных'
            self.logger.error(err_msg)
            self._clear_search_data()
            showerror(title=ERROR_MSG, message=err_msg)
        else:
            # Присвоение найденного пациента глобальной переменной пациента
            self.app.patient = patients[0]

            # Смена текста надписи пациента на главном экране на текущего
            text = (
                f'{self.app.patient.surname} {self.app.patient.name} '
                f'{self.app.patient.patronymic} '
                f'{self.app.patient.birth_date.strftime('%d.%m.%Y')}'
            )
            self.patient_label.set(text)

            # Внесение в лог
            self.logger.info('Загружен пациент из базы данных.')
            log_patient_attrs(
                self.app.patient,
                self.logger,
                self.app.patient.all_attrs
            )
    

    def _clear_search_data(self):
        '''Удаляет переменную пациента с неактуальными поисковыми данными'''
        self.patient_label.set(NO_PATIENT)
        delattr(self.app, 'patient')