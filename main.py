from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    # Get the form data
    server = request.form['server']
    database = request.form['database']
    username = request.form['username']
    password = request.form['password']

    # Define the connection string
    driver = '{ODBC Driver 17 for SQL Server}'
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    # Connect to the database
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        message = "Connected to the database!"
    except Exception as e:
        message = f"Error connecting to the database: {e}"

    # Render the result page
    return render_template('result.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)