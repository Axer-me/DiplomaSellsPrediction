import os
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

import model
import matplotlib.pyplot as plt

import preprocessing
from users import User, db
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

print(model.prediction_model.score(model.X_test, model.y_test))
print(123)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'diploma-work'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    users_list = User.query.order_by(User.id).all()
    roles = ['user', 'engineer','admin']
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_id = int(user_id)
        user = User.query.get(user_id)
        new_role = request.form.get('roles')
        if user:
            user.role=new_role
            db.session.commit()
        return redirect('/users')
    else: return render_template('users.html', roles=roles, users_list=users_list)

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
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if request.form.get('password_change'):
            password = request.form.get('password')
            password_again = request.form.get('password_again')
            if password == password_again and password and password_again:
                if not check_password_hash(current_user.password, password):
                    flash('Неверный пароль. Пожалуйста, попробуйте снова.')
                else:
                    current_user.password = generate_password_hash(password)
                    db.session.commit()
            else: flash('Пароли не совпадают.')
        elif request.form.get('about_change'):
            current_user.about_me = request.form.get('about_user')
            print('changed')
            db.session.commit()
        return redirect('/profile')
    return render_template('profile.html', name=current_user.name,
                           role=current_user.role, about=current_user.about_me)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')



@app.route('/main')
@login_required
def index():
    table_html = model.table_html
    return render_template('index.html', graph_path='/static/graph.png',
                           table_html=table_html)


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/')
def introduction():
    return render_template("introduction.html")


@app.route('/data', methods=['GET', 'POST'])
@login_required
def data_page():

    table_html = model.table_html

    return render_template('data.html', table_html=table_html)


@app.route('/data/full', methods=['GET', 'POST'])
@login_required
def data_full():
    temp_df1 = pd.read_excel(model.data_path)
    try:
        temp_df2 = pd.read_excel(r'my_resourses/Sells_new.xlsx')
        temp_df = pd.concat([temp_df1, temp_df2], ignore_index=True)
        temp_df = temp_df.reset_index(drop=True)
    except FileNotFoundError as ex:
        print(ex)
        temp_df = temp_df1
    html_table = temp_df.to_html(classes="dataframe")

    return render_template('data_full.html', table_html=html_table)

@app.route('/data/graphs', methods=['GET', 'POST'])
@login_required
def data_graphs_page():

    return render_template('graphs.html', graph_path='/static/graph.png')


@app.route('/data/graphs/options', methods=['GET', 'POST'])
@login_required
def graph_options():
    graph_types = ['Столбчатая диаграмма', 'Линейный график']
    col_options = set(model.X.columns)
    operation = ['sum', 'count', 'mean', 'max', 'min', 'none']
    if request.method == 'POST':
        graph_type = request.form['graph_types']
        col1 = request.form['col1']
        operation = request.form['operation']
        graph_data = model.data_preprocessed.groupby([col1])['Продажи, кг']
        if operation == 'sum':
            graph_data = graph_data.sum()
        elif operation == 'count':
            graph_data = graph_data.count()
        elif operation == 'mean':
            graph_data = graph_data.mean()
        elif operation == 'max':
            graph_data = graph_data.max()
        elif operation == 'min':
            graph_data = graph_data.min()
        else:
            graph_data = graph_data.count()
        graph_data.columns = [{operation}]
        if graph_type == 'Столбчатая диаграмма':
            graph_data = graph_data.sort_values(ascending=False).plot(kind='bar')
        elif graph_type == 'Линейный график':
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
    temp_data = model.load_df()
    prediction_type = ['На неделю', 'На месяц', 'На год']
    prediction_item_category = list(temp_data['Категория товара'].unique())
    prediction_item_value = list(temp_data['Товар'].unique())
    prediction_city_value = list(temp_data['Город'].unique())
    prediction_client_group_values = list(temp_data['Группа клиентов'].unique())
    prediction_format_values = list(temp_data['Формат точки'].unique())
    today = date.today()
    max_day = today + relativedelta(years=5)
    prediction_df = pd.DataFrame(columns=model.X.columns)
    if request.method == 'POST':
        if request.form["prediction_first_date"]:
            new_date = request.form["prediction_first_date"]
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
                               prediction_format_values=prediction_format_values, today=today, max_day=max_day)

@app.route('/predictions/table')
@login_required
def prediction_table():
    prediction_df = pd.read_excel('static/prediction.xlsx')
    html_table = prediction_df.to_html(classes="dataframe")

    return render_template('prediction_table.html', table_html=html_table)


@app.route('/data/predictions/model')
@login_required
def data_model_page():
    param_dict = {'colsample_bytree': model.cs_bytree, 'gamma': model.gam, 'learning_rate': model.lr,
                  'max_depth': model.m_depth, 'n_estimators': model.n_est, 'subsample': model.s_sample}
    html_table = pd.DataFrame([param_dict]).reset_index(drop=True)
    html_table.index = ['Значение' for existing_index_value in html_table.index]
    html_table = html_table.T.to_html(classes="dataframe")

    return render_template('model_page.html', table_html=html_table)

@app.route('/data/add_row', methods=['GET', 'POST'])
@login_required
def add_row():
    temp_data = model.load_df()
    prediction_item_category = list(temp_data['Категория товара'].unique())
    prediction_item_value = list(temp_data['Товар'].unique())
    prediction_city_value = list(temp_data['Город'].unique())
    prediction_client_group_values = list(temp_data['Группа клиентов'].unique())
    prediction_format_values = list(temp_data['Формат точки'].unique())
    today = date.today()
    avg_sell = round(temp_data['Продажи, кг'].mean())
    min_day = today - relativedelta(years=3)
    if request.method == 'POST':
        if request.form["prediction_first_date"]:
            day = request.form["prediction_first_date"]
        else:
            day = today
        if request.form['sells']:
            sell = request.form['sells']
        else:
            sell = avg_sell
        prediction_item_category = request.form['prediction_item_category']
        prediction_item_value = request.form["prediction_item_value"]
        prediction_city_value = request.form["prediction_city_value"]
        prediction_client_group_value = request.form["prediction_client_group_values"]
        prediction_format_value = request.form["prediction_format_values"]
        temp_dict = {'Дата': day, 'Категория товара': prediction_item_category,
                     'Товар': prediction_item_value, 'Город': prediction_city_value,
                     'Группа клиентов': prediction_client_group_value,
                     'Формат точки': prediction_format_value, 'Продажи, кг': sell}
        try:
            temp_df = pd.read_excel('my_resourses/Sells_new.xlsx')
            new_data = pd.concat([temp_df, pd.DataFrame([temp_dict])], ignore_index=True)
            new_data.to_excel('my_resourses/Sells_new.xlsx', index=False)
        except FileNotFoundError:
            new_data = pd.DataFrame([temp_dict])
            new_data.to_excel('my_resourses/Sells_new.xlsx', index=False)

        return redirect('/data/full')
    else:
        return render_template('add_row.html', min_day=min_day, avg_sell=avg_sell,
                               prediction_item_category=prediction_item_category,
                               prediction_item_value=prediction_item_value,
                               prediction_city_value=prediction_city_value,
                               prediction_client_group_values=prediction_client_group_values,
                               prediction_format_values=prediction_format_values, today=today)

@app.route('/data/predictions/model/fine-tuning')
@login_required
def model_fine_tuning():
    try:
        temp_df = pd.read_excel(r'my_resourses/Sells_new.xlsx')
        temp_df['Дата'] = temp_df['Дата'].astype('datetime64[ns]')
        temp_df = preprocessing.transform(temp_df)
        temp_df = preprocessing.scaling(temp_df)
        temp_x = temp_df.drop('Продажи, кг', axis=1)
        temp_y = temp_df['Продажи, кг']
        try:
            model.prediction_model.fit(temp_x, temp_y, xgb_model=model.prediction_model.get_booster())
            sells = pd.read_excel(r'my_resourses/Sells_new.xlsx')
            new_data = pd.concat([temp_df, sells], ignore_index=True)
            new_data = new_data.reset_index(drop=True)
            new_data.to_excel(r'my_resourses/Sells_new.xlsx')
            print(model.prediction_model.score(model.X_test, model.y_test))
            try:
                os.remove(r'my_resourses/Sells_new.xlsx')
            except FileNotFoundError as ex:
                print(ex)
            bool = True
        except Exception as ex:
            print(ex)
            bool = False
    except FileNotFoundError as ex:
        bool = False
        print(ex)

    return render_template('model_fine-tuning.html', bool=bool)




if __name__ == '__main__':
    with app.app_context():  # Needed for DB operations
        db.create_all()  # Creates the database and tables
    app.run(debug=True)
