'''Реализовано резервное копирование файла базы данных на сетевой папке и локальном компьютере'''

from datetime import datetime, timedelta
from pathlib import Path
import shutil
from tkinter.messagebox import showerror
import re

# Мои модули
from app_data import (
    DB_PATH_DIR, 
    DB_FILE_NAME, 
    ERROR_MSG,
    DATE_FILE_FORMAT,
)

class Backuper:
    '''Класс для бэкапа файла БД'''
    def __init__(self, app):
        # Получение логгера
        self.logger = app.logger

        # Получение сегодняшней даты
        self.today = datetime.today()

        # Количество дней сохранений
        self.backups_days = 7
        # Количество резервных копий (не менее)
        self.backups_count = 3
        
        # Имя файла и папки резервной копии
        self.prefix_file_name = 'dh_db_backup_at_'
        self.file_name = (
            f'{self.prefix_file_name}{self.today.strftime(DATE_FILE_FORMAT)}'
        )
        self.dir_name = 'dh_backup'
        
        # Путь к БД
        self.db_path_dir = Path(DB_PATH_DIR)
        self.db_path_file = self.db_path_dir / DB_FILE_NAME

        # Создание резервных копий и удаление устаревших
        self._create_server_backup()
        self._create_local_backup()


    def _create_server_backup(self):
        '''Создает резервную копию на сервере'''
        backup_file_server = self.db_path_dir / self.dir_name / self.file_name
        backup_dir_server = self.db_path_dir / self.dir_name
        self._create(backup_file_server)
        self._delete_old_backups(backup_dir_server)

    
    def _create_local_backup(self):
        '''Создает резервную копию на докальном диске'''
        # Путь к резервной копии
        backup_dir_local = (
            Path.home() / 'Documents' / 'HEP_cab_db' / self.dir_name
        )
        # Создание локальной папки
        try:
            backup_dir_local.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            self._error_handler(
                'Ошибка при создании локальной папки для резервных копий', err
            )
            return
            
        backup_file_local = backup_dir_local / self.file_name

        self._create(backup_file_local)
        self._delete_old_backups(backup_dir_local)


    def _create(self, backup_file):
        '''Создание резервной копии'''
        # Проверка наличия резервной копии сегодняшнего числа
        if backup_file.is_file():
            self.logger.info('Резервная копия БД уже существует')
            return
        
        # Создание резервной копии БД
        try:
            if not self.db_path_file.is_file():
                raise FileNotFoundError(
                    f'По пути {self.db_path_file} файл БД не найден'
                )
            shutil.copy(self.db_path_file, backup_file)
            self.logger.info(f'Создана резервная копия БД. Путь: {backup_file}')
        except Exception as err:
            self._error_handler(
                'Ошибка при создании резервной копии БД', err
            )

    
    def _delete_old_backups(self, backup_dir):
        '''Проверяет наличие и удаляет резервные копии старше 2 недель'''
        deleted_flag = False # Флаг о наличии удаленных файлов
        pattern = self.prefix_file_name + r'(\d{2}_\d{2}_\d{2})'

        # Проверка существования папки для бэкапа
        if not backup_dir.is_dir():
            self._error_handler(
                f'Пути {backup_dir} для бэкапа не существует'
            )
            return

        # Перебор всех имен файлов в папке с резервными копиями
        for name in (item.name for item in backup_dir.iterdir()):
            match = re.search(pattern, name)
            if match:
                created_date = datetime.strptime(
                    match.group(1), DATE_FILE_FORMAT
                )
                if (
                    created_date < self.today - timedelta(self.backups_days)
                    and len(tuple(backup_dir.iterdir())) > self.backups_count
                ):
                    file_path = backup_dir / name
                    file_path.unlink() # Удаление файла
                    self.logger.info(f'Файл {file_path} удален')
                    deleted_flag = True
        
        if not deleted_flag: # Если нет удаленных файлов
            self.logger.info('Файлы устаревших резервных копий не найдены')
        
    
    def _error_handler(self, err_msg, err=''):
        '''Выводит сообщения об ошибках и выводит их в лог'''
        if err: err_msg = f'{err_msg}: {err}'
        self.logger.error(err_msg)
        showerror(title=ERROR_MSG, message=f'{err_msg}. Смотрите лог')
