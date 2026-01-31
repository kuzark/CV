'''Использовал модифицированный мною паттерн «Наблюдатель» для последовательного изменения или добавления данных (текущая дата, данные врача и т. д.) в текст медицинского документа.'''

from handlers import TextHandler
from .random_vitals import RandomVitals
from .head_changers import WeekChanger, TitleChanger
from .treatment_changer import TreatmentChanger
from .signature import Signature

class MedDocChanger:
    def __init__(self, app):
        # Экземпляр приложения
        self.app = app
        # Список для хранения методов изменения дневника
        self.changers = []
        # Инициализация обработчика текста
        self.text_handler = TextHandler(app.text)


    def add_changer(self, method):
        '''Добавление функций для изменения дневника'''
        self.changers.append(method)

    
    def get(self):
        '''Получение текста дневника из текстового поля'''
        self.meddoc = self.app.text.get('1.0', 'end')


    def rebuild(self):
        '''Изменение дневника'''
        # Исходный дневник отправлен в лог для сравнения
        self.app.logger.info('\nИсходный дневник:\n%s', self.meddoc)
        # Запуск цикла методов для изменения
        for method in self.changers:
            # Запись дневника до изменения методом
            previous_meddoc = self.meddoc
            report = 'Дневник не изменен.'
            try:
                self.meddoc = method(self.meddoc)
            except Exception as err:
                self.app.logger.error(f'Неизвестная ошибка: {err}')
                break
            else:
                # Если дневник изменен в лог уходит текст дневника
                if self.meddoc != previous_meddoc:
                    report = self.meddoc
                # Запись измененного дневника в лог
                self.app.logger.info(
                    '\nМетод: %s\n%s',
                    method.__name__,
                    report
                )

    
    def publish(self):
        '''Вставка дневника в текстовое поле'''
        self.app.text.delete('1.0', 'end')
        self.app.text.insert('1.0', self.meddoc)
        self.app.text.tag_add('main' ,'1.0', 'end')
        self.app.text.tag_add('title' ,'1.0', '2.0')


    def format(self):
        '''Форматирование дневника в текстовом поле'''
        self.text_handler.empty_strings_cutter()
        self.text_handler.paragraphs_selector()


def meddoc_rebuilder(app):
    '''Функция для изменения дневника'''
    # Инициализация классов
    rebuilder = MedDocChanger(app)
    random_vitals = RandomVitals(app)
    week_changer = WeekChanger(app)
    title_changer = TitleChanger(app)
    treatment_changer = TreatmentChanger(app)
    signature = Signature(app)
    
    # Регистрация методов для изменения дневника
    rebuilder.add_changer(title_changer.change_title)
    rebuilder.add_changer(week_changer.change_week_period)
    rebuilder.add_changer(week_changer.change_week_number)
    rebuilder.add_changer(random_vitals.generate_RR)
    rebuilder.add_changer(random_vitals.generate_HR)
    rebuilder.add_changer(random_vitals.generate_BP)
    rebuilder.add_changer(treatment_changer.change_week_treatment)
    rebuilder.add_changer(treatment_changer.change_recomendation_treatment)
    rebuilder.add_changer(signature.generate_signature)

    # Получение текста дневника из текстового поля
    rebuilder.get()

    # Изменение дневника
    rebuilder.rebuild()

    # Вставка дневника в текстовое поле
    rebuilder.publish()

    # Форматирование дневника в текстовом поле
    rebuilder.format()
