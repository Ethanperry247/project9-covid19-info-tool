# Database imports
import pg8000

# Secret passwords
import getpass

# JSON
import json

# Server imports 
from flask import Flask, request, url_for, render_template, jsonify
app = Flask(__name__)

# Database class
class Database:

    username = 'Not Logged In.'
    password = ''
    db = None
    cursor = None
    result = None

    def __init__(self):
        super().__init__()

    def login(self, username, password):

        # Set username and password.
        self.username = username
        self.password = password

        # Attempt to log into database.
        try:
            self.db = pg8000.connect(user=username, password=password, host='bartik.mines.edu', database='csci403')
            self.cursor = self.db.cursor()
            return True # Return true for a success.
        except pg8000.Error as e: # Otherwise reset the username and password and return false.
            self.username = 'Not Logged In.'
            self.password = ''
            return False
    
    # Execute queries with this method.
    def execute(self, query, args=None):
        if args is None:
            try: # Execute the query if possible and fill the result variable of this class.
                self.cursor.execute(query)
                self.result = self.cursor.fetchall()
                return True
            except pg8000.Error as e: # Otherwise, report a database error to the server.
                print("-+-Database Error-+-")
                print(e)
                self.result = 'Invalid query.'
                return False
        else:
            try: # Execute the query if possible and fill the result variable of this class.
                self.cursor.execute(query, args)
                self.result = self.cursor.fetchall()
                return True
            except pg8000.Error as e: # Otherwise, report a database error to the server.
                print("-+-Database Error-+-")
                print(e)
                self.result = 'Invalid query.'
                return False

    # Data can be retrieved after executing a query.
    def get_result(self):
        return self.result

    def get_username(self):
        return self.username

# Database to be used by the app.
db = Database()

@app.route('/')
def main():
    return render_template('index.html')

@app.route("/search", methods=['POST', 'GET'])
def search():
    username = db.get_username()
    query = 'SELECT DISTINCT state FROM covid_data ORDER BY state'
    # Attempt to execute several queries.
    db.execute(query)
    states = db.get_result()


    query = 'SELECT DISTINCT county FROM covid_data ORDER BY county'
    db.execute(query)
    counties = db.get_result()

    if request.method == 'POST':
        print("County request for " + str(request.form['select']))

    return render_template('search.html', username=username, states=states, counties=counties)

@app.route('/state', methods=['POST', 'GET'])
def state():
    result = ''
    state = ''
    username = db.get_username()
    if request.method == 'POST':
        state = request.form['state']
        query = 'SELECT DISTINCT county FROM covid_data WHERE state=%s ORDER BY county'
        db.execute(query, [state])
        result = db.get_result()

        query = 'SELECT SUM(cases) FROM (SELECT DISTINCT MAX(date), MAX(cases) AS cases, state, county FROM covid_data WHERE state=%s GROUP BY state, county) as temporary'
        db.execute(query, [state])
        cases = db.get_result()

        query = 'SELECT SUM(deaths) FROM (SELECT DISTINCT MAX(date), MAX(deaths) AS deaths, state, county FROM covid_data WHERE state=%s GROUP BY state, county) as temporary'
        db.execute(query, [state])
        deaths = db.get_result()

    return render_template('state.html', username=username, state=state, counties=result, cases=cases, deaths=deaths)

@app.route('/county', methods=['POST', 'GET'])
def county():
    county = ''
    cases = ''
    deaths = ''
    state = ''
    username = db.get_username()
    if request.method == 'POST':
        try:
            county = request.form['county']
            state = request.form['state']
            query = 'SELECT MAX(cases) FROM covid_data WHERE state=%s AND county=%s GROUP BY county'
            db.execute(query, [state, county])
            cases = db.get_result()
            
            query = 'SELECT MAX(deaths) FROM covid_data WHERE state=%s AND county=%s GROUP BY county'
            db.execute(query, [state, county])
            deaths = db.get_result()
            return render_template('county.html', state=state, county=county, username=username, cases=cases, deaths=deaths)
        except:
            return ('Invalid County or State Name.')
    

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.login(username, password):
            return render_template('login.html', username=username)
        else:
            return ('Invalid username or password.')
    return render_template('login.html', username=db.get_username())

@app.route("/searchbar")
def searchbar():
    return render_template ('searchbar.html', username=db.get_username())

@app.route("/statistics")
def statistics():
    state = ''
    county = ''
    state_cases = 0
    county_cases = 0

    # Query will grab the three states with the most cases from the most recent date.
    query = """SELECT MAX(cases), state FROM 
                    (SELECT SUM(cases) AS cases, state FROM 
                        (SELECT DISTINCT MAX(date), MAX(cases) AS cases, covid_data.state, county FROM covid_data GROUP BY state, county) 
                    as inside GROUP BY state) 
                as outside GROUP BY state, cases ORDER BY cases DESC LIMIT 3;
            """
    db.execute(query)
    state = db.get_result()

    # Query will grab the three counties with the most cases from the most recent date.
    query = "SELECT cases, county, state FROM (SELECT DISTINCT MAX(date), MAX(cases) AS cases, state, county FROM covid_data GROUP BY state, county ORDER BY cases DESC LIMIT 3) as temporary;"
    db.execute(query)
    county = db.get_result()

    # Query will grab the average cases per county from the most recent date.
    query = "SELECT AVG(cases) FROM (SELECT DISTINCT MAX(date), MAX(cases) AS cases, state, county FROM covid_data GROUP BY state, county ORDER BY cases) as temporary"
    db.execute(query)
    result = db.get_result()
    county_average = round(result[0][0])

    query = """SELECT AVG(cases) FROM 
                    (SELECT SUM(cases) AS cases, state FROM 
                        (SELECT DISTINCT MAX(date), MAX(cases) AS cases, covid_data.state, county FROM covid_data GROUP BY state, county) 
                    as inside GROUP BY state) 
                as outside
            """
    db.execute(query)
    result = db.get_result()
    state_average = round(result[0][0])

    query = "SELECT SUM(cases) FROM (SELECT DISTINCT MAX(date), MAX(cases) AS cases, state, county FROM covid_data GROUP BY state, county ORDER BY cases) as temporary"
    db.execute(query)
    result = db.get_result()
    total = result[0][0]

    return render_template('statistics.html', state=state, county=county, county_average=county_average, state_average=state_average, total=total)
