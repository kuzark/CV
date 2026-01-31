'''Класс для генерации заключения по значениям показателей биохимического анализа крови'''

from math import floor

class BiochemicalBloodAnalysis:
    '''Класс, содержащий заключения по БАК'''
    def __init__(self, gender):
        # Пол пациента
        self.gender = gender
        # Общий билирубин выше нормы
        self.high_total_bilirubin = False
        # Азотемия
        self.nitrogenemia = False

        # Список методов
        self._methods = [
            self.total_protein,
            self.albumin,
            self.total_bilirubin,
            self.conjugated_bilirubin,
            self.alat,
            self.asat,
            self.alkaline_phosphatase,
            self.gamma_glutamyltranspeptidase,
            self.glucosa,
            self.urea,
            self.сreatinine,
            self.cholesterol,
        ]

    
    def __getitem__(self, idx):
        '''Получение метода по ключу'''
        return self._methods[idx]


    def __iter__(self):
        '''Возвращает генератор методов'''
        return iter(self._methods)


    def total_protein(self, result):
        if result < 66:
            return 'гипопротеинемия'
    

    def albumin(self, result):
        if result < 35:
            return 'гипоальбуминемия'
    

    def total_bilirubin(self, result):
        if result > 21:
            self.high_total_bilirubin = True
            return 'гипербилирубинемия'


    def conjugated_bilirubin(self, result):
        if result > 5.1 and self.high_total_bilirubin:
            return ' преимущественно за счет прямого билирубина'
    

    def alat(self, result):
        if result > 41:
            min_norm = floor(result / 41)
            max_norm = min_norm + 1
            conclusion_ALT = f'АлАТ от {min_norm} '
            conclusion_ALT += f'до {max_norm} норм '
            conclusion_ALT = self._virus_activity(
                min_norm, max_norm, conclusion_ALT
            )
            return conclusion_ALT
    

    def _virus_activity(self, min, max, conclusion_ALT):
        activity = 'выраженной активности процесса)'
        if min == 1 and max == 2:
            activity = '(минимально ' + activity
            return conclusion_ALT + activity
        if min == 2 and max == 3:
            activity = '(слабо ' + activity
            return conclusion_ALT + activity
        if min >= 3 and max <= 5:
            activity = '(умеренно ' + activity
            return conclusion_ALT + activity
        if min >= 5:
            activity = '(' + activity
            return conclusion_ALT + activity
    

    def asat(self, result):
        if result > 37:
            return 'АсАТ выше нормы'
    

    def alkaline_phosphatase(self, result):
        if (
            self.gender == 'male' and result > 128
            or self.gender == 'female' and result > 98
        ):
            return 'ЩФ выше нормы'
    

    def gamma_glutamyltranspeptidase(self, result):
        if (
            self.gender == 'male' and result > 49
            or self.gender == 'female' and result > 32
        ):
            return 'ГГТП выше нормы'
    

    def glucosa(self, result):
        if result > 5.9:
            return 'гипергликемия'


    def urea(self, result):
        if result > 8.3:
            self.nitrogenemia = True
        
    
    def сreatinine(self, result):
        if (
            self.gender == 'male' and result > 115
            or self.gender == 'female' and result > 97
        ):
            self.nitrogenemia = True
        if self.nitrogenemia:
            return 'гиперазотемия'


    def cholesterol(self, result):
        if result > 5.2:
            return 'гиперхолестеринемия'
