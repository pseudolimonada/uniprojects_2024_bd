
import flask
import psycopg2
import src.db as db
import src.validator as validator
from src.utils import config, StatusCodes, UserDetails, logger

app = flask.Flask(__name__)

#todo maybe implement a db connection pool

@app.route('/')
def landing_page():
    return """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """

# Call this function when you want to use the db to get a db connection
def get_db():
    if 'db_con' not in flask.g:
        flask.g.db_con = db.create_connection(config['DB_NAME'], config['DB_HOST'], config['DB_PORT'], config['DB_USER'], config['DB_PASS'])
    return flask.g.db_con

# This function gets called when the request is done to close db connection
@app.teardown_appcontext
def close_db(e=None):
    db_con = flask.g.pop('db_con', None)

    if db_con is not None:
        db_con.close()

@app.route('/dbproj/register/<string:user_type>', methods=['POST'])
def register(user_type):
    payload = flask.request.get_json()

    logger.info('POST /register')
    logger.debug(f'POST /register - payload received: {payload}')

    # check if user type is valid
    if (validator.user_type(user_type) == False):
        response = {'status': StatusCodes['api_error'], 'errors': 'Invalid user type'}
        return flask.jsonify(response)
    
    # check if all required fields are present
    missing_args = validator.user_register_details(user_type, payload)
    if len(missing_args) != 0:
        response = {'status': StatusCodes['api_error'], 'errors': f'Missing arguments: {', '.join(missing_args)}'}
        return flask.jsonify(response)
    
    # add to register
    try:
        db.register_user(get_db(), user_type, payload)
        response = {'status': StatusCodes['success'], 'results': f'Good job fam'}
    except [Exception,psycopg2.DatabaseError] as e:
        logger.error(f"Error: {e}")
        response = {'status': StatusCodes['internal_error'], 'errors': str(e)}
    
    logger.debug(f'POST /register - response: {response}')
    return flask.jsonify(response)


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

@app.route('/dbproj/top3', methods=['GET'])
def list_top3_patients():
    logger.info('GET /top3')
    try:
        db.get_top3_patients(get_db())
    except Exception as e:
        logger.error(f"Error: {e}")
        return {'status': StatusCodes['internal_error'], 'errors': str(e)}

    return {'status': StatusCodes['success'], 'results': 'Top 3 patients listed'}
    pass

# @app.route('/dbproj/daily/<string:date>', methods=['GET'])
# def daily_summary(date):
#     # Daily summary logic here
#     pass

# @app.route('/dbproj/report', methods=['GET'])
# def generate_monthly_report():
#     # Monthly report generation logic here
#     pass