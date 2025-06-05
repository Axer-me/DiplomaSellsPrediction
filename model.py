import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import preprocessing
from xgboost import XGBRegressor


data_path = r'my_resourses/Sells.xlsx'
data = pd.read_excel(data_path)
print(data.info())

data_preprocessed = preprocessing.transform(data)

data_scaled = preprocessing.scaling(data_preprocessed)

X = data_scaled.drop('Продажи, кг', axis=1)
y = data_scaled['Продажи, кг']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.19, random_state=1)

prediction_model = XGBRegressor(colsample_bytree = 1, gamma = 0, learning_rate = 0.1,
                     max_depth = 9, n_estimators = 100, subsample = 0.8)
prediction_model.fit(X_train, y_train)
