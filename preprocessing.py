# from sklearn.base import BaseEstimator, TransformerMixin
from datetime import datetime, timedelta

import holidays
from sklearn.preprocessing import StandardScaler


def transform(data):
    """
    Обычная transorm-функция, методы из которой я до этого протестировал в ноутбуке
    """

    item_category_values = {1: 2, 4: 1, 14: 3, 15: 4}
    item_values = {29: 1, 30: 2, 31: 3, 527: 4, 336: 5,
                   505: 6, 276: 7, 291: 8, 749: 9, 560: 10}
    city_values = {1: 1, 8: 2, 7: 3, 3: 4, 15: 5,
                   5: 6, 2: 7, 6: 8, 9: 9, 4: 10, 11: 11}
    client_group_values = {2: 1, 159: 2}
    format_values = {1: 1, 8: 2, 3: 3, 2: 4}
    data = data.replace({'Категория товара': item_category_values,
                         'Товар': item_values, 'Город': city_values,
                         'Группа клиентов': client_group_values, 'Формат точки': format_values})

    holiday_years = ['2020', '2021', '2022', '2023']
    holidays_base = holidays.RU(years=holiday_years).items()
    before_holidays_delta_days = 1
    before_holidays_delta = timedelta(days=before_holidays_delta_days)
    holiday_dates = list()
    for holiday_date, holiday_name in holidays_base:
        holiday_dates.append(holiday_date)
        holiday_dates.append(holiday_date - before_holidays_delta)
    holiday_dates = list(dict.fromkeys(holiday_dates))

    data['Праздник'] = data.apply(lambda x: 1 if (datetime.date(x['Дата']) in holiday_dates) else 0, axis=1)
    data['Год'] = data['Дата'].dt.year
    data['Месяц'] = data['Дата'].dt.month
    data['День'] = data['Дата'].dt.day
    data['День недели'] = data['Дата'].dt.day_of_week
    data['Выходной'] = data.apply(lambda x: 1 if (x['День недели'] >= 5) else 0, axis=1)
    data['Квартал'] = data['Дата'].dt.quarter
    data = data.drop(columns=['Дата'])
    return data

def scaling(data):
    numerical_cols = ['Год', 'Месяц', 'День', 'День недели', 'Квартал']
    scaler = StandardScaler()
    data_scaled = data
    data_scaled[numerical_cols] = scaler.fit_transform(data[numerical_cols])
    return data_scaled