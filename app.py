from datetime import datetime, date, time
import os
import time

import MySQLdb.cursors
import re
import hashlib

from flask import Flask, render_template, request, redirect, url_for, session

from flask_mysqldb import MySQL, MySQLdb

from bs4 import BeautifulSoup

app = Flask(__name__)

app.secret_key = '\xf0?a\x9a\\\xff\xd4;\x0c\xcbHi'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234567890'
app.config['MYSQL_DB'] = 'dostavo4ka'
app_root = os.path.dirname(os.path.abspath(__file__))

mysql = MySQL(app)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if session.get('loggedin'):
        return redirect(url_for('couriers'))
    # if session['logged_in'] or not session.new:
    #     return redirect(url_for('couriers'))
    # elif
    elif request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        hash_password = hashlib.sha256(password.encode())
        password = hash_password.hexdigest()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = % s AND password = % s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['email'] = account['email']
            session['building'] = account['building']
            session['photo'] = account['photo']
            session['courier'] = account['courier']
            return redirect('couriers')
        else:
            msg = 'Неправильный логин / пароль'
    return render_template('auto.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if session.get('loggedin'):
        return redirect(url_for('couriers'))
    elif request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'building' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        building = request.form['building']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = % s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Аккаунт уже существует'
        elif not re.match(r'[A-Za-z]+\.[A-Za-z]{2,3}+@students.dvfu.ru', email):
            msg = 'Неправильный адрес почты'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Логин должен содержать только английские буквы и цифры'
        elif not username or not password or not email or not building:
            msg = 'Пожалуйста, заполните все поля'
        else:
            hash_password = hashlib.sha256(password.encode())
            cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s, % s, DEFAULT, DEFAULT)',
                           (username, hash_password.hexdigest(), email, building))
            mysql.connection.commit()
            msg = 'Вы успешно зарегистрировались'
    elif request.method == 'POST':
        msg = 'Пожалуйста, заполните все поля'
    return render_template('reg.html', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/couriers')
def couriers():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    else:
        today = str(date.today())
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM couriers WHERE today = % s', [today])
        courier = cursor.fetchall()
        for el in courier:
            delivery_time_start = str(el['delivery_time_start']).split(":")
            el['delivery_time_start'] = delivery_time_start[0] + ":" + delivery_time_start[1]
            delivery_time_end = str(el['delivery_time_end']).split(":")
            el['delivery_time_end'] = delivery_time_end[0] + ":" + delivery_time_end[1]
        return render_template('couriers.html', courier=courier)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    msg = ''
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    else:
        target = os.path.join(app_root, 'static/img/icons/')
        if not os.path.isdir(target):
            os.makedirs(target)
        if request.method == 'POST':
            if 'courier' in request.form:
                is_checked = bool(request.form.get('courier'))
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET courier = % s WHERE id = % s', (is_checked, session['id']))
                mysql.connection.commit()
                session['courier'] = is_checked
            else:
                is_checked = False
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET courier = % s WHERE id = % s', (is_checked, session['id']))
                mysql.connection.commit()
                session['courier'] = is_checked
            if 'username' in request.form:
                username = request.form['username']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE username = % s and id != % s', (username, session['id']))
                account = cursor.fetchone()
                if account:
                    msg = 'Такой логин занят'
                elif not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Логин должен содержать только английские буквы и цифры'
                else:
                    cursor.execute('UPDATE users SET username = % s WHERE id = % s', (username, session['id']))
                    mysql.connection.commit()
                    session['username'] = username
            if 'email' in request.form:
                email = request.form['email']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM users WHERE email = % s and id != % s', (email, session['id']))
                account = cursor.fetchone()
                if account:
                    msg = 'Такая почта занята'
                elif not re.match(r'[A-Za-z]+\.[A-Za-z]{2,3}+@students.dvfu.ru', email):
                    msg = 'Неправильный адрес почты'
                else:
                    cursor.execute('UPDATE users SET email = % s WHERE id = % s', (email, session['id']))
                    mysql.connection.commit()
                session['email'] = email
            if 'building' in request.form:
                building = request.form['building']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET building = % s WHERE id = % s', (building, session['id']))
                mysql.connection.commit()
                session['building'] = building
            if 'contact' in request.form:
                contact = request.form['contact']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET contact = % s WHERE id = % s', (contact, session['id']))
                mysql.connection.commit()
                session['contact'] = contact
            file = request.files['file']
            if file.filename != '':
                file_name = str(time.time()) + file.filename
                destination = '/'.join([target, file_name])
                file.save(destination)
                path = 'img/icons/' + file_name
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET photo = % s WHERE id = % s', (path, session['id']))
                mysql.connection.commit()
                session['photo'] = path
                msg = "Данные успешно обновлены"
            else:
                if msg == '':
                    msg = "Данные успешно обновлены"
                return render_template('profile.html', msg=msg)

        return render_template('profile.html', msg=msg)


@app.route('/chat')
@app.route('/requests')
def chat():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    elif not session['courier']:
        return redirect(url_for('couriers'))
    else:
        today = str(date.today())
        print(today)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM couriers WHERE courier_id = % s and today = % s', (session['id'], today))
        tcouriers = cursor.fetchall()
        cursor.execute('SELECT * FROM couriers WHERE courier_id = % s and today != % s', (session['id'], today))
        lcouriers = cursor.fetchall()
        for el in tcouriers:
            delivery_time_start = str(el['delivery_time_start']).split(":")
            el['delivery_time_start'] = delivery_time_start[0] + ":" + delivery_time_start[1]
            delivery_time_end = str(el['delivery_time_end']).split(":")
            el['delivery_time_end'] = delivery_time_end[0] + ":" + delivery_time_end[1]
        for el in lcouriers:
            delivery_time_start = str(el['delivery_time_start']).split(":")
            el['delivery_time_start'] = delivery_time_start[0] + ":" + delivery_time_start[1]
            delivery_time_end = str(el['delivery_time_end']).split(":")
            el['delivery_time_end'] = delivery_time_end[0] + ":" + delivery_time_end[1]
        return render_template('chat.html', tcouriers=tcouriers, lcouriers=lcouriers, today=today)


@app.route('/requests/<couriers_id>/<id>', methods=['GET', 'POST'])
def status(couriers_id, id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    elif not session['courier']:
        return redirect(url_for('couriers'))

    if request.method == 'POST' and request.form['action'] == 'yes':
        cursor.execute('UPDATE orders SET status = % s WHERE id = % s', ("Принят в работу", id))
        mysql.connection.commit()
    elif request.form['action'] == 'no':
        cursor.execute('UPDATE orders SET status = % s WHERE id = % s', ("Отклонен курьером", id))
        mysql.connection.commit()
    elif request.form['action'] == 'picked_up':
        cursor.execute('UPDATE orders SET status = % s WHERE id = % s', ("В процессе доставки", id))
        mysql.connection.commit()
    elif request.form['action'] == 'delivered':
        cursor.execute('UPDATE orders SET status = % s WHERE id = % s', ("Успешно доставлен", id))
        mysql.connection.commit()
    return redirect('/requests/' + couriers_id)


@app.route('/requests/<couriers_id>')
def request_orders(couriers_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE courier_id = % s and couriers_id = %s', (session['id'], couriers_id))
    orders = cursor.fetchall()
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    elif not session['courier']:
        return redirect(url_for('couriers'))
    else:
        for el in orders:
            cursor.execute('SELECT * FROM users WHERE id = % s', [el['orderer_id']])
            orderer = cursor.fetchone()
            el['name'] = orderer['username']
        return render_template('request_orders.html', orders=orders)


@app.route('/orders')
def orders():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM orders WHERE orderer_id = % s', [session['id']])
        orders = cursor.fetchall()
        for el in orders:
            cursor.execute('SELECT * FROM couriers WHERE courier_id = % s', [el['courier_id']])
            courier = cursor.fetchone()
            el['price'] = courier['price']
            el['name'] = courier['name']
            el['ccontact'] = courier['contact']
        return render_template('orders.html', orders=orders)


@app.route('/orders/<id>', methods=['GET', 'POST'])
def cancelorder(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    if request.method == 'POST' and request.form['action'] == 'cancel':
        cursor.execute('UPDATE orders SET status = % s WHERE id = % s', ("Отменен заказчиком", id))
        mysql.connection.commit()
    return redirect(url_for('orders'))


@app.route('/couriers/<id>')
def courier(id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    else:
        timern = datetime.strptime(str(datetime.now())[11:], "%H:%M:%S.%f")
        print(timern)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM couriers WHERE id = % s', [id])
        courier = cursor.fetchone()
        delivery_time_start = str(courier['delivery_time_start']).split(":")
        courier['delivery_time_start'] = delivery_time_start[0] + ":" + delivery_time_start[1]
        delivery_time_end = str(courier['delivery_time_end']).split(":")
        courier['delivery_time_end'] = delivery_time_end[0] + ":" + delivery_time_end[1]
        closing_time = datetime.strptime(str(courier['closing_time']), "%H:%M:%S")
        delta = timern - closing_time
        timeout = delta.total_seconds()
        return render_template('courier.html', courier=courier, timeout=timeout)


@app.route('/courier/close/<couriers_id>')
def close_orders(couriers_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE couriers SET status = % s WHERE id = % s', ("0", couriers_id))
    mysql.connection.commit()
    return redirect(url_for('couriers'))


@app.route('/form', methods=['GET', 'POST'])
def form():
    msg = ''
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST' and 'dts' in request.form and 'dte' in request.form and 'price' in request.form and 'places' in request.form and 'closing_time' in request.form and 'contact' in request.form:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            courier_id = session['id']
            name = session['username']
            today = str(date.today())
            dts = request.form['dts']
            dte = request.form['dte']
            closing_time = request.form['closing_time']
            price = request.form['price']
            places = request.form['places']
            contact = request.form['contact']
            comm = request.form['comm'].capitalize()
            if 'limit' in request.form:
                limit = request.form['limit']
                cursor.execute(
                    'INSERT INTO couriers VALUES (NULL, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s)',
                    (courier_id, name, contact, price, today, dts, dte, closing_time, places, comm, "0", limit, "1"))
                mysql.connection.commit()
            else:
                limit = request.form['limit']
                cursor.execute(
                    'INSERT INTO couriers VALUES (NULL, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, NULL, % s)',
                    (courier_id, name, contact, price, today, dts, dte, closing_time, places, comm, "0", "1"))
                mysql.connection.commit()
            return redirect('couriers')
        elif request.method == 'POST':
            msg = 'Пожалуйста, заполните все поля'

    return render_template('anket.html', msg=msg)


@app.route('/order/<couriers_id>/', methods=['GET', 'POST'])
def order(couriers_id):
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM couriers WHERE id = % s', [couriers_id])
    courier = cursor.fetchone()
    if request.method == 'POST' and 'building' in request.form and 'place' in request.form and 'amount' in request.form and 'order_num' in request.form and 'contact' in request.form:
        couriers_id = courier['id']
        orderer_id = session['id']
        building = request.form['building']
        place = request.form['place']
        amount = request.form['amount']
        order_num = request.form['order_num']
        contact = request.form['contact']
        comm = request.form['comm'].capitalize()
        now = datetime.now()
        cursor.execute('INSERT INTO orders VALUES (NULL, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, DEFAULT)',
                       (couriers_id, courier['courier_id'], orderer_id, building, place, amount, order_num, contact,
                        comm, now))
        mysql.connection.commit()
        courier['orders'] = courier['orders'] + 1
        cursor.execute('UPDATE couriers SET orders = % s WHERE id = % s', (courier['orders'], [couriers_id]))
        mysql.connection.commit()
        if courier['orders'] == courier['limits']:
            cursor.execute('UPDATE couriers SET status = % s WHERE id = % s', ("0", [couriers_id]))
            mysql.connection.commit()
        return redirect('/orders')
    elif request.method == 'POST':
        msg = 'Пожалуйста, заполните все поля'

    return render_template('order.html', msg=msg, courier=courier, id=id)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', )


if __name__ == '__main__':
    app.run(debug=True)
