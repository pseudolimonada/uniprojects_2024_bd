import flask
import logging
import psycopg2
import time
import psycopg2
import jwt
import datetime

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

## ACCESS

def db_connection():
    db = psycopg2.connect(
        user='dbproj',
        password='1234',
        host='127.0.0.1',
        port='5432',
        database='dbproj'
    )
    return db

## ENDPOINTS

@app.route('/')
def register():
    return """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """

@app.route('dbproj/register/<string:user_type>', methods=['POST'])
def register(user_type):
    # Registration logic here
    pass

@app.route('dbproj/user', methods=['PUT'])
def authenticate():
    # Authentication logic here
    pass

@app.route('/appointment', methods=['POST'])
def schedule_appointment():
    # Appointment scheduling logic here
    pass

@app.route('/appointments/<int:patient_user_id>', methods=['GET'])
def see_appointments(patient_user_id):
    # Fetch appointments logic here
    pass

@app.route('/surgery', methods=['POST'])
@app.route('/surgery/<int:hospitalization_id>', methods=['POST'])
def schedule_surgery(hospitalization_id=None):
    # Surgery scheduling logic here
    pass

@app.route('/dbproj/prescriptions/<int:person_id>', methods=['GET'])
def get_prescriptions(person_id):
    # Fetch prescriptions logic here
    pass

@app.route('/dbproj/prescription/', methods=['POST'])
def add_prescriptions():
    # Add prescriptions logic here
    pass

@app.route('/dbproj/bills/<int:bill_id>', methods=['POST'])
def execute_payment(bill_id):
    # Payment execution logic here
    pass

@app.route('/dbproj/top3', methods=['GET'])
def list_top3_patients():
    # Fetch top 3 patients logic here
    pass

@app.route('/dbproj/daily/<string:date>', methods=['GET'])
def daily_summary(date):
    # Daily summary logic here
    pass

@app.route('/dbproj/report', methods=['GET'])
def generate_monthly_report():
    # Monthly report generation logic here
    pass

if __name__ == '__main__':
    app.run(debug=True, port=8080)