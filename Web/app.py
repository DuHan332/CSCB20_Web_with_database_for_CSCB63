import sqlite3
from flask import Flask, render_template, request, g, session, redirect, \
    url_for

DATABASE = './assignment3.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


app = Flask(__name__)
app.secret_key = 'somesecretkeylol'



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()


@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = session['name']
    role = session['role']
    return render_template("index.html", name=name, role=role)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        db.row_factory = make_dicts
        sql = """
            SELECT *
            FROM users
            """
        results = query_db(sql, args=(), one=False)
        db.close()
        if request.form['username'] == '':
            return render_template("error.html",
                                   message="Username cannot be empty")
        if request.form['password'] == '':
            return render_template("error.html",
                                   message="Password cannot be empty")
        username = request.form['username']
        for result in results:
            if result['username'] == username:
                if result['password'] == request.form['password']:
                    session['username'] = username
                    session['role'] = result['role']
                    session['name'] = result['name']
                    return redirect(url_for('index'))
                return render_template("error.html",
                                       message="Incorrect Password")
        return render_template("error.html", message="Incorrect Username")

    elif 'username' in session:
        return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route('/assignment')
def assignment():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("assignment.html", name=session['name'],
                           role=session['role'])


@app.route('/syllabus')
def syllabus():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("syllabus.html", name=session['name'],
                           role=session['role'])


@app.route('/labs')
def labs():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("labs.html", name=session['name'],
                           role=session['role'])


@app.route('/courseteam')
def courseteam():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("courseteam.html", name=session['name'],
                           role=session['role'])


@app.route('/calendar')
def calendar():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("calendar.html", name=session['name'],
                           role=session['role'])


@app.route('/StudentGrades', methods=['GET', 'POST'])
def studentgrades():
    if session['role'] == 1:
        return render_template('error.html',
                               message="You are not allowed to visit this page")
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        db = get_db()
        if request.form['project'] == '':
            return render_template('error.html',
                                   message="Please choose a project")
        project = request.form['project']
        if request.form['reason'] == '':
            return render_template('error.html', message="Please give a reason")
        reason = request.form['reason']
        sql = "SELECT * FROM remarkrequest"
        results = query_db(sql, args=(), one=False)
        for result in results:
            if result[0] == session['username']:
                if result[1] == project:
                    return render_template('error.html',
                                           message="You can only submit one request for each project")
        insert2 = "INSERT INTO remarkrequest (username, project, reason) " + \
                  "VALUES ('" + username + "','" + project + "','" + reason + "');"
        query_db(insert2)
        db.commit()
        db.close()
        return redirect(url_for('studentgrades'))
    else:
        username = session['username']
        sql2 = "SELECT * FROM grades WHERE username = '"  + username + "';"
        result = query_db(sql2, args=(), one=True)
        return render_template("studentgrades.html", name=session['name'],
                               role=session['role'], result=result)


@app.route('/instructorgrades', methods=['GET', 'POST'])
def instructorgrades():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['role'] == 0:
        return render_template('error.html',
                               message="You are not allowed to visit this page")
    if request.method == 'POST':
        if request.form['id'] == '':
            return render_template('error.html',
                                   message="StudentID cannot be empty")
        if request.form['project'] == '':
            return render_template('error.html',
                                   message="Please choose a project")
        if request.form['newmark'] == '':
            return render_template('error.html',
                                   message="Please Enter a new mark")
        if not request.form['newmark'].isnumeric():
            return render_template('error.html',
                                   message="New mark should be a number")
        db = get_db()
        studentid = request.form['id']
        project = request.form['project']
        newmark = request.form['newmark']
        exist = False
        sql = "SELECT username FROM grades;"
        results1 = query_db(sql, args=(), one=False)
        for result in results1:
            if studentid == result[0]:
                exist = True
        if not exist:
            return render_template('error.html',
                                   message="This student does not exist")
        modify = "UPDATE grades set " + project + "=" + newmark + " WHERE username = '" + studentid + "';"
        query_db(modify)
        db.commit()
        db.close()
        return redirect(url_for('instructorgrades'))
    sql = "SELECT username, name, assignment1, assignment2, assignment3, assignment4, termtest1 , termtest2, termtest3, finalexam FROM users NATURAL JOIN grades;"
    results = query_db(sql, args=(), one=False)
    return render_template("instructorgrades.html", name=session['name'],
                           role=session['role'], result=results)


@app.route('/viewremarks')
def viewremarks():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['role'] == 0:
        return render_template('error.html',
                               message="You are not allowed to visit this page")
    sql = "SELECT username, name, project, reason FROM remarkrequest NATURAL JOIN users"
    result = query_db(sql, args=(), one=False)
    return render_template('viewremarks.html', result=result, name=session['name'], role=session['role'])


@app.route('/anonymousfeedback', methods=['GET', 'POST'])
def anonymousfeedback():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['role'] == 1:
        return render_template('error.html',
                               message="You are not allowed to visit this page")
    if request.method == 'POST':
        if request.form['q1'] == '' and request.form['q2'] == '' and \
                request.form['q3'] == '' and request.form['q4'] == '':
            return render_template('error.html',
                                   message="Please fill at least one blank")
        if request.form['instructor'] == '':
            return render_template('error.html',
                                   message="Please choose a instructor")
        sql = "SELECT * FROM feedbacks"
        results = query_db(sql)
        for result in results:
            if request.form['instructor'] == result[0] and \
                    request.form['q1'] == result[1] and \
                    request.form['q2'] == result[2] and \
                    request.form['q3'] == result[3] and \
                    request.form['q4'] == result[4]:
                return render_template("error.html",
                                       message="We already have the exactly same feedback")
        db = get_db()
        name = request.form['instructor']
        q1 = request.form['q1']
        q2 = request.form['q2']
        q3 = request.form['q3']
        q4 = request.form['q4']
        insert = "INSERT INTO feedbacks (instructor, question1, question2, question3, question4) VALUES (?,?,?,?,?)"
        query_db(insert, args=(name, q1, q2, q3, q4))
        db.commit()
        db.close()
        return redirect(url_for('anonymousfeedback'))
    sql = "SELECT name FROM users WHERE role = 1;"
    result = query_db(sql, args=(), one=False)
    return render_template('anonymousfeedback.html', result=result, name=session['name'], role=session['role'])


@app.route('/reviewfeedback')
def reviewfeedback():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['role'] == 0:
        return render_template('error.html',
                               message="You are not allowed to visit this page")
    sql = "SELECT question1, question2, question3, question4 FROM feedbacks WHERE instructor = '" + \
          session['name'] + "';"
    result = query_db(sql, args=(), one=False)
    return render_template('reviewfeedback.html', result=result, name=session['name'], role=session['role'])


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('name', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.form['username'] == '':
            return render_template("error.html",
                                   message="Username cannot be empty")
        else:
            username = request.form['username']
        if request.form['password'] == '':
            return render_template("error.html",
                                   message="Password cannot be empty")
        else:
            password = request.form['password']
        if request.form['password'] != request.form['password2']:
            return render_template("error.html",
                                   message="2 passwords does not match")
        if request.form['name'] == '':
            return render_template("error.html",
                                   message="name cannot be empty")
        else:
            name = request.form['name']
        if request.form['role'] == '':
            return render_template("error.html",
                                   message="please select a role")
        else:
            if request.form['role'] == 'Professor':
                role = '1'
            else:
                role = '0'
        db = get_db()
        db.row_factory = make_dicts
        query = """
            SELECT *
            FROM users
            """
        results = query_db(query, args=(), one=False)
        for result in results:
            if result['username'] == username:
                return render_template("error.html",
                                       message="This username is used")
        insert = "INSERT INTO users (username, name, role, password) " + \
                 "VALUES ( '" + username + "','" + name + "'," + role + ",'" \
                 + password + "');"
        query_db(insert)
        if role == '0':
            insert2 = "INSERT INTO grades (username, assignment1, assignment2, " \
                      + "assignment3, assignment4, termtest1, termtest2, " \
                      + "termtest3, finalexam) VALUES ('" + username + "',0,0," \
                                                                      "0,0,0," \
                                                                      "0,0,0) "
            query_db(insert2)
        db.commit()
        db.close()
        session['username'] = username
        session['role'] = int(role)
        session['name'] = name
        return redirect(url_for('index'))

    elif 'username' in session:
        return redirect(url_for('index'))
    else:
        return render_template("signup.html")


if __name__ == "__main__":
    app.run()