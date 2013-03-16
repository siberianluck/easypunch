from __future__ import division
import sqlite3
import hashlib
import datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, render_template, g, Response, session, jsonify, flash
from werkzeug import secure_filename

app = Flask(__name__)

app.config.from_pyfile('config.cfg');

DATABASE = app.config['DATABASE']
AUTH_USER = app.config['AUTH_USER']
AUTH_PW = app.config['AUTH_PW']

app.secret_key = app.config['SECRET_KEY']

"""
Database connection
"""
def connect_db():
    return sqlite3.connect(DATABASE)

@app.before_request
def before_request():
    g.db = connect_db();

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

"""
DB Helper
"""
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

"""
Authentication
"""
def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PW

def authenticate():
    return Response(
    'Restricted Area!\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth', methods=['POST'])
def auth_employee():
    if request.method == 'POST' and request.form['accessCode']:
        employeeId = query_db('SELECT employeeId, employeeName FROM employee WHERE accessCode = ?  LIMIT 1', [request.form['accessCode']], True)
        if employeeId:
            session['employeeId'] = int(employeeId['employeeId'])
            session['employeeName'] = employeeId['employeeName']
            return redirect(url_for('punch'))
    return redirect(url_for('index'))

@app.route('/punch', methods=['POST', 'GET'])
def punch():
    recent_punch = query_db(
                'SELECT punchIn, punchOut, cardId FROM card WHERE employeeId = ? AND punchOut ISNULL ORDER BY cardId DESC LIMIT 1',
                [session.get('employeeId')],
                True
            )

    if request.method == 'POST':
        if request.form['date_submit'] != '':
            punch_time = request.form['date_submit'] + ' ' + request.form['time']
            redirect_route = 'punch'
        else:
            now = datetime.datetime.now()
            punch_time = now.strftime("%Y-%m-%d %H:%M:%S")
            redirect_route = 'index'

        if recent_punch:
            query_db('UPDATE card SET punchOut = ? WHERE cardId = ?', [punch_time, recent_punch['cardId']])
            g.db.commit()
            flash('You have successfully punched out!')
        else:
            query_db('INSERT INTO card (employeeId, punchIn) VALUES (?, ?)', [session.get('employeeId'), punch_time])
            g.db.commit()
            flash('You have successfully punched in!')
        return redirect(url_for(redirect_route))
    else:
        if recent_punch and 'punchIn' in recent_punch:
            punch_type = 'Out'
        else:
            punch_type = 'In'
        return render_template('punch.html', punch_type=punch_type, name=session.get('employeeName'))

@app.route('/new_emp', methods=["POST"])
@requires_auth
def new_emp():
    query_db('INSERT INTO employee (employeeName, accessCode) VALUES (?, ?)', [request.form['empName'], request.form['empAccess']])
    g.db.commit()
    return redirect(url_for('admin'))

@app.route('/update_emp', methods=["POST"])
def update_emp():
    if request.form['type'] == 'e':
        query_db('UPDATE employee SET employeeName = ? WHERE employeeId = ?', [request.form['value'], request.form['empId']])
        g.db.commit()
    elif request.form['type'] == 'a':
        query_db('UPDATE employee SET accessCode = ?  WHERE employeeId = ?', [request.form['value'], request.form['empId']])
        g.db.commit()
    return jsonify(result=True)

@app.route('/admin', methods=["GET", "POST"])
@requires_auth
def admin():
    employees = query_db('SELECT employeeId, employeeName, accessCode FROM employee')

    if request.form and request.form['startDate_submit'] != '' and request.form['endDate_submit'] != '':
        endDate = datetime.datetime.strptime(request.form['endDate_submit'], '%Y-%m-%d')
        startDate = datetime.datetime.strptime(request.form['startDate_submit'], '%Y-%m-%d')
    else:
        endDate = datetime.datetime.now()
        startDate = endDate - datetime.timedelta(weeks=2)

    cards = {}
    hoursSum = {}
    for employee in employees:
        card = query_db(
                "SELECT * FROM card WHERE employeeId = ? AND strftime('%s', punchIn) BETWEEN strftime('%s', ?) AND strftime('%s', ?)",
                [employee['employeeId'], startDate, endDate])

        cards[employee['employeeId']] = []

        hoursSum[employee['employeeId']] = 0;

        for time in card:
            if time['punchIn'] is not None and time['punchOut'] is not None:
                punchIn = datetime.datetime.strptime(time['punchIn'], '%Y-%m-%d %H:%M:%S')
                punchOut = datetime.datetime.strptime(time['punchOut'], '%Y-%m-%d %H:%M:%S')
                hoursObj = punchOut - punchIn

                cards[employee['employeeId']].append({'date' : punchIn.strftime('%m-%d-%Y'), 'punchIn' : punchIn.strftime('%H:%M:%S'),
                    'punchOut' : punchOut.strftime('%H:%M:%S') , 'hours' : '%0.2f' % (((hoursObj.days * 86400) + hoursObj.seconds) / 3600)})

                hoursSum[employee['employeeId']] += (hoursObj.days * 86400) + hoursObj.seconds

        hoursSum[employee['employeeId']] = '%0.2f' % (hoursSum[employee['employeeId']] / 3600)

    return render_template('admin.html', employees = employees, cards = cards, hoursSum = hoursSum)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
