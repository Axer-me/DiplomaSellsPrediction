import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import preprocessing
from xgboost import XGBRegressor

table_html = None
data_path = r'my_resourses/Sells.xlsx'
def load_df():
    data = pd.read_excel(data_path)
    global table_html
    table_html= data.sample(10).to_html(classes="dataframe")
    return data


data_preprocessed = preprocessing.transform(load_df())

data_scaled = preprocessing.scaling(data_preprocessed)

X = data_scaled.drop('Продажи, кг', axis=1)
y = data_scaled['Продажи, кг']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.19, random_state=1)
cs_bytree = 1
gam = 0
lr = 0.1
m_depth = 9
n_est = 100
s_sample = 0.8
prediction_model = XGBRegressor(colsample_bytree = cs_bytree, gamma = gam, learning_rate = lr,
                     max_depth = m_depth, n_estimators = n_est, subsample = s_sample)
prediction_model.fit(X_train, y_train)

group8 = data_preprocessed.loc[data_preprocessed['Категория товара'] != -1, :].groupby(['Категория товара'])[
        ['Продажи, кг']].sum()
x = list(group8.index)
for i in range(group8['Продажи, кг'].count()):
    x[i] = str(x[i])
y = list()
for i in range(group8['Продажи, кг'].count()):
    y.append(group8.values[i, 0])
plt.bar(x, y, label='Продажи по категориям')
plt.xlabel('Категория товара')
plt.ylabel('Продажи, 10*млн кг')
plt.title('Столбчатая диаграмма продаж')
plt.savefig('static/graph.png')
