
import flask
import jwt

import src.db as db
import src.validator as validator

from src.utils import logger, STATUS_CODES
from src.api import app, token_required
from psycopg2 import DatabaseError

# app is being initialized in src/api.py
# token_required is a decorator that checks if token is valid, otherwise returns 401 immediately
# - it also decodes a user id/type (encoded during authentication), and feeds it back to the function as kwargs (keyword parameters)
# - the "login_id=None, login_types=None" in functions is just a way to tell the function will receive this from the decorator

@app.route('/')
def landing_page():
    return """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """

@app.route('/dbproj/user', methods=['PUT'])
def authenticate_user():
    # authentication logic here
    payload = flask.request.get_json()
    logger.info('POST /register')
    logger.debug(f'POST /register - payload received: {payload}')

    try: 
        validator.user_login_details(payload) # check if payload has username and password

        login_id, login_types = db.login_user(flask.g.db_con, payload)
        token = jwt.encode({'login_id': login_id, 'login_types': login_types}, app.config['SECRET_KEY'])
        response = {'status': STATUS_CODES['success'],'results': f'auth token {token}'}

    except ValueError as e:
        response = {'status': STATUS_CODES['api_error'], 'errors': str(e)}
    except (Exception, DatabaseError) as e:
        logger.error(f"Error: {e}")
        response = {'status': STATUS_CODES['internal_error'], 'errors': str(e)}

    logger.debug(f'POST /register - response: {response}')
    return flask.jsonify(response)

@app.route('/dbproj/register/<string:user_type>', methods=['POST'])
@token_required
def register(user_type, login_id=None, login_types=None):
    payload = flask.request.get_json()
    logger.info('POST /register')
    logger.debug(f'POST /register - payload received: {payload}')

    # check if user type is valid
    try:
        validator.user_type(user_type) # check if user_type is valid
        validator.user_register_details(user_type, payload) # check if payload has all the required fields

        register_id = db.register_user(flask.g.db_con, user_type, payload)
        response = {'status': STATUS_CODES['success'], 'results': f'id {register_id} registered successfully'}

    except ValueError as e:
        logger.error(f"Error: {e}")
        response = {'status': STATUS_CODES['api_error'], 'errors': str(e)}

    except (Exception, DatabaseError) as e:
        logger.error(f"Error: {e}")
        response = {'status': STATUS_CODES['internal_error'],'errors': str(e)}
    
    logger.debug(f'POST /register - response: {response}')
    return flask.jsonify(response)


@app.route('/dbproj/appointment', methods=['POST'])
@token_required
def schedule_appointment(login_id=None, login_types=None):
    # appointment scheduling logic here
    user_id
    pass


@app.route('/dbproj/appointments/<patient_user_id>', methods=['GET'])
@token_required
def see_appointments(login_id=None, login_types=None):
    # logic to list all appointments here
    pass


@app.route('/dbproj/surgery', methods=['POST'])
@app.route('/dbproj/surgery/<hospitalization_id>', methods=['POST'])
@token_required
def schedule_surgery(hospitalization_id=None, login_id=None, login_types=None):
    # surgery scheduling logic here
    pass


@app.route('/dbproj/prescriptions/<person_id>', methods=['GET'])
@token_required
def get_prescriptions(login_id=None, login_types=None):
    # logic to get prescriptions here
    pass


@app.route('/dbproj/prescription/', methods=['POST'])
@token_required
def add_prescriptions(login_id=None, login_types=None):
    # logic to add prescriptions here
    pass


@app.route('/dbproj/bills/<bill_id>', methods=['POST'])
@token_required
def execute_payment(bill_id, login_id=None, login_types=None):
    # payment execution logic here
    pass


@app.route('/dbproj/top3', methods=['GET'])
@token_required
def list_top3_patients(login_id=None, login_types=None):
    # logic to list top 3 patients here
    pass


@app.route('/dbproj/daily/<date>', methods=['GET'])
@token_required
def daily_summary(date, login_id=None, login_types=None):
    # logic to get daily summary here
    pass


@app.route('/dbproj/report', methods=['GET'])
@token_required
def generate_monthly_report(login_id=None, login_types=None):
    # logic to generate monthly report here
    pass