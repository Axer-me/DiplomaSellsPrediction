from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from numpy import datetime64
from sqlalchemy.sql.functions import current_date
from werkzeug.security import check_password_hash, generate_password_hash

import model
import matplotlib.pyplot as plt

import preprocessing
from users import User, db
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

print(model.prediction_model.score(model.X_test, model.y_test))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'diploma-work'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

print(model.data.index.max())
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Неверный email или пароль. Пожалуйста, попробуйте снова.')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect('/main')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')



@app.route('/main')
@app.route('/home')
@login_required
def index():
    return render_template('index.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/')
def introduction():
    return render_template('introduction.html')


@app.route('/data', methods=['GET', 'POST'])
@login_required
def data_page():
    group8 = model.data_preprocessed.loc[model.data_preprocessed['Категория товара'] != -1, :].groupby(['Категория товара'])[
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
    html_table = model.data.sample(10).to_html(classes="dataframe")

    return render_template('data.html', table_html=html_table)


@app.route('/data/full', methods=['GET', 'POST'])
@login_required
def data_full():
    html_table = model.data.to_html(classes="dataframe")

    return render_template('data_full.html', table_html=html_table)

@app.route('/data/graphs', methods=['GET', 'POST'])
@login_required
def data_graphs_page():

    return render_template('graphs.html', graph_path='/static/graph.png')


@app.route('/data/graphs/options', methods=['GET', 'POST'])
@login_required
def graph_options():
    graph_types = set(['Столбчатая диаграмма', 'Линейный график'])
    col_options = set(model.X.columns)
    print(col_options)
    operation = set(['sum', 'count', 'mean', 'max', 'min', 'none'])
    if request.method == 'POST':
        graph_type = request.form['graph_types']
        col1 = request.form['col1']
        operation = request.form['operation']
        if graph_type == 'Столбчатая диаграмма':
            graph_data = model.data_preprocessed.groupby([col1])['Продажи, кг']
            if operation == 'sum': graph_data = graph_data.sum()
            elif operation == 'count': graph_data = graph_data.count()
            elif operation == 'mean': graph_data = graph_data.mean()
            elif operation == 'max': graph_data = graph_data.max()
            elif operation == 'min': graph_data = graph_data.min()
            else: graph_data = graph_data.count()
            graph_data.columns = [{operation}]
            graph_data = graph_data.sort_values(ascending=False).plot(kind='bar')
            graph_data.get_figure().savefig('static/graph.png')
            plt.close()
        elif graph_type == 'Линейный график':
            graph_data = model.data_preprocessed.groupby([col1])['Продажи, кг']
            if operation == 'sum': graph_data = graph_data.sum()
            elif operation == 'count': graph_data = graph_data.count()
            elif operation == 'mean': graph_data = graph_data.mean()
            elif operation == 'max': graph_data = graph_data.max()
            elif operation == 'min': graph_data = graph_data.min()
            else: graph_data = graph_data.count()
            graph_data.columns = [{operation}]
            graph_data = graph_data.sort_values(ascending=False).plot(kind='line')
            graph_data.get_figure().savefig('static/graph.png')
            plt.close()
        return redirect('/data/graphs')
    else:
        return render_template('graph_options.html', graph_types=graph_types,
                               col_options=col_options, operation=operation)

@app.route('/predictions', methods=['GET', 'POST'])
@login_required
def predictions():
    prediction_type = ['На неделю', 'На месяц', 'На год']
    prediction_item_category = list(model.data['Категория товара'].unique())
    prediction_item_value = list(model.data['Товар'].unique())
    prediction_city_value = list(model.data['Город'].unique())
    prediction_client_group_values = list(model.data['Группа клиентов'].unique())
    prediction_format_values = list(model.data['Формат точки'].unique())
    today = date.today()
    prediction_df = pd.DataFrame(columns=model.X.columns)
    if request.method == 'POST':
        if request.form["prediction_first_date"]:
            day = request.form["prediction_first_date"]
        else:
            new_date = today
            prediction_item_category = request.form['prediction_item_category']
            prediction_item_value = request.form["prediction_item_value"]
            prediction_city_value = request.form["prediction_city_value"]
            prediction_client_group_value = request.form["prediction_client_group_values"]
            prediction_format_value = request.form["prediction_format_values"]
            prediction_type = request.form["prediction_type"]
            if prediction_type == 'На неделю':
                new_date += relativedelta(days=+7)
            elif prediction_type == 'На месяц':
                new_date += relativedelta(months=+1)
            elif prediction_type == 'На год':
                new_date += relativedelta(years=+1)
            current_date = today
            while current_date < new_date:
                cur_dict = {'Дата': current_date, 'Категория товара': int(prediction_item_category),
                            'Товар': int(prediction_item_value), 'Город': int(prediction_city_value),
                            'Группа клиентов': int(prediction_client_group_value), 'Формат точки': int(prediction_format_value)}
                prediction_df = pd.concat([prediction_df,pd.DataFrame([cur_dict])], ignore_index=True)
                prediction_df['Дата'] = prediction_df['Дата'].astype('datetime64[ns]')
                current_date += relativedelta(days=+1)
            prediction_df = preprocessing.transform(prediction_df)
            prediction_df_scaled = prediction_df.copy()
            prediction_df_scaled = preprocessing.scaling(prediction_df_scaled)
            prediction = model.prediction_model.predict(prediction_df_scaled)
            prediction = pd.Series(prediction)
            prediction.name = 'Продажи, кг'
            prediction_df = pd.concat([prediction_df, pd.Series(prediction)], axis=1)

            prediction_df.to_excel('static/prediction.xlsx', index=False)

        return redirect('/predictions/table')
    else:
        return render_template('predictions.html', prediction_type=prediction_type,
                               prediction_item_category=prediction_item_category,
                               prediction_item_value=prediction_item_value,
                               prediction_city_value=prediction_city_value,
                               prediction_client_group_values=prediction_client_group_values,
                               prediction_format_values=prediction_format_values, today=today)

@app.route('/predictions/table')
@login_required
def prediction_table():
    prediction_df = pd.read_excel('static/prediction.xlsx')
    print(prediction_df.columns)
    html_table = prediction_df.to_html(classes="dataframe")

    return render_template('prediction_table.html', table_html=html_table)


@app.route('/predictions/model')
@login_required
def data_model_page():
    param_dict = {'colsample_bytree': model.cs_bytree, 'gamma': model.gam, 'learning_rate': model.lr,
                  'max_depth': model.m_depth, 'n_estimators': model.n_est, 'subsample': model.s_sample}
    html_table = pd.DataFrame(param_dict).to_html(classes="dataframe")

    return render_template('model_page.html', table_html=html_table)




if __name__ == '__main__':
    with app.app_context():  # Needed for DB operations
        db.create_all()  # Creates the database and tables
    app.run(debug=True)