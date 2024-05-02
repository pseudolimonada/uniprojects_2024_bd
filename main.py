from dotenv import load_dotenv
load_dotenv()

import flask
import logging
import psycopg2
import time
import datetime
import os

app = flask.Flask(__name__)


DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_PORT")

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

UserDetails = {
    'patient': ['username','password','name','address','cc_number','nif_number','birthdate'],
    'assistant': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date']],
    'doctor': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date'],'license','specialization'],
    'nurse': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date']],
}

## ACCESS

def db_connection():
    db = psycopg2.connect(
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )
    return db

## ENDPOINTS

@app.route('/')
def landing_page():
    return """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """

@app.route('/dbproj/register/<string:user_type>', methods=['POST'])
def register(user_type):
    logger.info('POST /register')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /register - payload received: {payload}')
    
    flag = 0
    for user in UserDetails.keys():
        if user == user_type:
            flag = 1
            break
    if flag == 0:
        response = {'status': StatusCodes['api_error'], 'results': 'you stich... invalid user type'}
        return response

    missing_args = []
    for user_detail in UserDetails[user_type]:
            if type(user_detail) == str:
                 if user_detail not in payload:
                      missing_args.append(user_detail)
            if type(user_detail) == list:
                 for detail_detail in user_detail:
                      if detail_detail not in payload:
                           missing_args.append(detail_detail)
    
    if len(missing_args) != 0:
        missing_args_str = ', '.join(missing_args)
        response = {'status': StatusCodes['api_error'], 'results': f'Missing arguments: {missing_args_str}'}
        return response
    
    return {'status': StatusCodes['success'], 'results': f'Good job fam'}


# @app.route('/dbproj/user', methods=['PUT'])
# def authenticate():
#     # Authentication logic here
#     pass

# @app.route('/dbproj/appointment', methods=['POST'])
# def schedule_appointment():
    # Appointment scheduling logic here
#     pass

# @app.route('/dbproj/appointments/<int:patient_user_id>', methods=['GET'])
# def see_appointments(patient_user_id):
#     # Fetch appointments logic here
#     pass

# @app.route('/dbproj/surgery', methods=['POST'])
# @app.route('/surgery/<int:hospitalization_id>', methods=['POST'])
# def schedule_surgery(hospitalization_id=None):
#     # Surgery scheduling logic here
#     pass

# @app.route('/dbproj/prescriptions/<int:person_id>', methods=['GET'])
# def get_prescriptions(person_id):
#     # Fetch prescriptions logic here
#     pass

# @app.route('/dbproj/prescription/', methods=['POST'])
# def add_prescriptions():
#     # Add prescriptions logic here
#     pass

# @app.route('/dbproj/bills/<int:bill_id>', methods=['POST'])
# def execute_payment(bill_id):
#     # Payment execution logic here
#     pass

# @app.route('/dbproj/top3', methods=['GET'])
# def list_top3_patients():
#     # Fetch top 3 patients logic here
#     pass

# @app.route('/dbproj/daily/<string:date>', methods=['GET'])
# def daily_summary(date):
#     # Daily summary logic here
#     pass

# @app.route('/dbproj/report', methods=['GET'])
# def generate_monthly_report():
#     # Monthly report generation logic here
#     pass

if __name__ == '__main__':
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    #create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    app.run(host=APP_HOST, debug=True, threaded=True, port=APP_PORT)
    logger.info(f'API v1.0 online: http://{APP_HOST}:{APP_PORT}')
