import logging
import time
import datetime
import os
import sys 

import flask
import psycopg2
from dotenv import dotenv_values

app = flask.Flask(__name__)


def load_config() -> dict:
    try:
        config = dotenv_values(".env")
        parsed_config = {
            'DB_USER': config['DB_USER'],
            'DB_PASS': config['DB_PASS'],
            'DB_HOST': config['DB_HOST'],
            'DB_PORT': config['DB_PORT'],
            'DB_NAME': config['DB_NAME'],
            'APP_HOST': config['APP_HOST'],
            'APP_PORT': config['APP_PORT']
        }
        return parsed_config
    except KeyError as e:
        logger.error(f"Missing config key: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error converting config value to number: {str(e)}")
        sys.exit(1)


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

def db_connection(db_name, db_host, db_port, db_user, db_pass):
    db = psycopg2.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        database=db_name
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

    conn = db_connection(config['DB_NAME'], config['DB_HOST'], config['DB_PORT'], config['DB_USER'], config['DB_PASS'])
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
    logging.basicConfig(filename='log_file.log', level=logging.DEBUG, force=True, filemode='a')
    #add formatter with date and time

    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    config = load_config()
    app.run(host=config['APP_HOST'], debug=True, threaded=True, port=config['APP_PORT'])
    logger.info(f'API v1.0 online: http://{config['APP_HOST']}:{config['APP_PORT']}')
