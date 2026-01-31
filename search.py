'''Для анализа результатов анализов пациента необходимо их значения ввести в поля формы либо вручную, либо воспользовавшись автозаполнением. 
Для функции автозаполнения реализован поиск значений показателей биохимического анализа пациента в датафрейме загруженного из CSV-файла. 
Пользователь вводит фамилию, инициалы и дату рождения пациента в формате: ФАМИЛИЯ ИО ГГГГ, при этом поиск можно начать уже с ввода первых букв фамилии, 
если по введенной комбинации будет получено несколько пациентов, программа просит пользователя ввести больше символов. Для клинического анализа крови 
реализована схема поиска по значениям анализов, которые пользователь вводит в поле первого показателя, так как анализатор не выдает данные для инициализации пациента. 
Если по значению первого показателя найдено 1 совпадение, выполняется автозаполнение, если 2 и более совпадений, пользователю предлагается ввести значение следующего 
показателя и так далее, до получения только 1 совпадения.'''

from tkinter import END
from tkinter.messagebox import (
    showerror,
    showwarning, 
    showinfo, 
    askyesno,
)
import pandas as pd

# Мои модули
from app_data import (
    Paraclinics,
    INFO_MSG,
    WARNING_MSG,
    ERROR_MSG,
)
from handlers import (
    validate_float,
    validate_nulls,
    str_to_float,
)

class AnalysisSearch:
    '''Находит анализы конкретного человека, формирует список результатов
    и заполняет поля ввода'''
    
    def __init__(self, a_results, a_tab, logger):
        # Логгер
        self.logger = logger
        # Инициализация класса с показателями анализов
        self.paraclinics = Paraclinics()
        # Доступ к загруженным результатам анализов
        self.a_results = a_results
        # Доступ к экземпляру вкладки
        self.tab = a_tab
        # Анализ
        self.analys = a_tab.note_name
        # Атрибут для хранения датафрейма КАК, в котором происходит поиск
        self._df = self.a_results[self.analys].df
        # Индекс столбца, по которому происходит поиск
        self.idx_col_search = 0
        # Сообщения об ошибках
        self.missed_column_message = 'Отсутствует столбец: "{err}"'
        self.unknown_error_message = 'Неизвестная ошибка: "{err}"'


    def analysis_search_BAB(self):
        '''Поиск по биохимическому анализу крови'''
        # Получение генератора названий столбцов необходимых для поиска
        find_cols = (val[1] for val in self.paraclinics[self.analys].values())
        # Поиск по данным пациента
        patient = self.tab.patient_init.get().upper()
        finded_df = self._df[self._df['ID'].str.contains(patient)]
        # Формирование списка с анализами найденного пациента
        finded_list = self._check_finded_df(finded_df, find_cols)
        # Автозаполнение полей с анализами
        if finded_list:
            self._complete_finded_results(finded_list)


    def analysis_search_CAB(self):
        '''Поиск по клиническому анализу крови'''
        # Получение списка названий столбцов необходимых для поиска
        find_cols = [
            val[1] 
            for val in self.paraclinics[self.analys].values()
            if val[1] != ''
        ]
        # Получение списка названий полей ввода
        entry_names = [name for name in self.paraclinics[self.analys].keys()]
        # Получение искомого результата анализа из поля с вкладки с анализами
        # И его валидация
        result = self._get_entry_value(entry_names)
        # Поиск по столбцу и возврат датафрейма, содержащего только строку
        # с найденным пациентом
        if result:
            finded_df = self._find_result_CAB(result, find_cols)
        else:
            return
        # Формирование списка с анализами из строки датафрейма
        if finded_df is not None:
            finded_list = self._check_finded_df(finded_df, find_cols)
        else:
            return
        # Автозаполнение полей с анализами
        if finded_list:
            self._complete_finded_results(finded_list)


    def _get_entry_value(self, entry_names):
        '''Получение искомого результата анализа из поля с вкладки с анализами
        и его валидация'''
        # Считывание строки с поля с индексом поиска
        entry = self.tab.entries[self.idx_col_search]
        result = entry.get()
        
        # Проверка на соответствие строки десятичной дроби и не нулю
        if validate_float(result) or validate_nulls(result):
            err_text = 'Вводимые значения должны быть в виде десятичной '
            err_text += 'дроби, разделенной точкой или запятой!'
            showerror(title=ERROR_MSG, message=err_text)
            entry.delete(0, END)
            entry.insert(0, 'ERROR')
            return
        
        # Если поле ввода пустое
        if result == '':
            err_text = f'Поиск по полю "{entry_names[self.idx_col_search]}"'
            showerror(title=ERROR_MSG, message=err_text)
            return
        
        # Успешное завершение проверок, возврат считанного значения
        return result


    def _find_result_CAB(self, result, find_cols):
        '''Выполняет поиск по КАК и формирует список с анализами (Series) 
        конкретного пациента'''
        # Поиск по столбцу
        try:
            finded_df = self._df[
                self._df[find_cols[self.idx_col_search]] == str_to_float(
                    [result]
                )[0]
            ]
            return finded_df
        # Если столбец не найден
        except KeyError as err:
            msg = self.missed_column_message.format(err=err.args[0])
            self.logger.warning(msg)
            showwarning(title=WARNING_MSG, message=msg)
            self._ask_to_continue_search()
        # Неизвестная ошибка
        except Exception as err:
            msg = self.unknown_error_message.format(err=err)
            self.logger.error(msg)
            showerror(title=ERROR_MSG, message=msg)


    def _check_finded_df(self, finded_df, find_cols):    
        '''Проверяет количество найденных в датафрейме строк 
        и формирование списка найденных показателей анализов'''
        # Если результат не найден
        if len(finded_df.index) == 0:
            showinfo(title=INFO_MSG, message='Результат не найден')
            if self.analys == 'КАК':
                self._ask_to_continue_search()
        # Если найден один пациент
        elif len(finded_df.index) == 1:
            # Заполнение столбцов без значения нулями
            finded_df = finded_df.fillna(0)
            
            # Формирование списка объектов Series с показателями анализов
            finded_list = self._create_series(finded_df, find_cols)
            
            # Если КАК - сброс поиска
            if self.analys == 'КАК': 
                self._reset_search()
            return finded_list
        # Если найдено более двух пациентов
        else:
            # В КАК если совпадение у нескольких пациентов, то уже по 
            # отфильтрованному датафрейму будет заново проходить поиск уже
            # по следующему показателю анализа
            if self.analys == 'КАК':    
                self.idx_col_search += 1
                self._df = finded_df
                add_msg = 'Заполните следующее поле'
            # В БАК поиск происходит по дополненным данным пациента
            else:
                add_msg = 'Введите больше данных'
            msg = f'Множественное совпадение. {add_msg}'
            showinfo(title=INFO_MSG, message=msg)

    
    def _create_series(self, finded_df, find_cols):
        '''Формирует объекты Series, 
        где одна строка (найденный пациент), 
        состоящая из имени показателя анализа и его значения.
        '''
        for col in find_cols:
            try:
                series = finded_df[col]
            # Если отсутствует столбец вывод ошибки,
            # но запись столбца как пустого и продолжение цикла
            except KeyError as err:
                series = pd.Series({col: 0})
                msg = self.missed_column_message.format(err=err.args[0])
                self.logger.warning(msg)
                showwarning(title=WARNING_MSG, message=msg)
            # Неизвестная ошибка
            except Exception as err:
                msg = self.unknown_error_message.format(err=err)
                self.logger.error(msg)
                showerror(title=ERROR_MSG, message=msg)
                return
                
            # Возврат объекта Series
            yield series


    def _ask_to_continue_search(self):
        '''Выводит окно с вопросом о продолжении поиска по следующему 
        показателю и в зависимости от ответа меняет атрибуты экземпляра'''
        result = askyesno(
            title='Подтверждение операции',
            message='Продолжить поиск по следующему показателю?'
        )
        # При продолжении поиска датафрейм исходный индекс показателя +1
        if result: 
            self.idx_col_search += 1
            # Если индекс вышел за пределы допустимых для поиска показателей
            if self.idx_col_search > (len(self.paraclinics['КАК']) - 2):
                msg = 'Выход за пределы доступных для поиска показателей.'
                showerror(
                    title=ERROR_MSG, 
                    message=msg,
                    detail='Поиск сброшен и возвращен к первому показателю.'
                )
                self._reset_search()

        # При остановке поиска возврат к первому показателю и исходному df
        else: self._reset_search()

    
    def _reset_search(self):
        '''Сбрасывает индекс показателей до 0 и возвращает исходный датафрейм'''
        self.idx_col_search = 0
        self._df = self.a_results[self.analys].df


    def _complete_finded_results(self, finded_list):
        '''Заполняет поля ввода во вкладке найденными результатами анализов'''
        for i, series in enumerate(finded_list):
            # Очистка поля ввода
            self.tab.entries[i].delete(0, END)
            # Считывание показателя со списка результатов, если 0
            # замена на пустую строку
            result = series.iloc[0]
            if result == 0:
                result = ''
            # Ввод в поле ввода показателя анализа
            self.tab.entries[i].insert(0, result)
