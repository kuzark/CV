'''Публикация новых сборок автоматизирована через GitHub CLI.'''
'''Модуль для публикации релиза'''
import subprocess
from datetime import datetime
from app_data import (
    CURRENT_VERSION,
    REPO_PUBLIC_NAME,
    NAME_EXE,
)

# Получение текущей даты и времени
now = datetime.now()
date_time_str = now.strftime('%d-%m-%Y %H:%M:%S')

# Создание и отправка релиза
try:
    subprocess.run(
        [
            'gh', 'release', 'create',
            CURRENT_VERSION,
            '--repo', f'kuzark/{REPO_PUBLIC_NAME}',
            '--notes', f'Release {CURRENT_VERSION} {date_time_str}',
            '--title', f'Release {CURRENT_VERSION} {date_time_str}',
            f'dist/{NAME_EXE}-{CURRENT_VERSION}.exe'
        ], check=True
    )
    print(f"Релиз {CURRENT_VERSION} создан, файл загружен!")
except subprocess.CalledProcessError as e:
    print(f"Ошибка: {e}")
