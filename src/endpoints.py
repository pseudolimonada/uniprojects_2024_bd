
from flask import Flask, g, request
import src.db as db
import src.validator as validator
from src.utils import config, StatusCodes, UserDetails, logger

app = Flask(__name__)

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
    if 'db_con' not in g:
        g.db_con = db.create_connection(config['DB_NAME'], config['DB_HOST'], config['DB_PORT'], config['DB_USER'], config['DB_PASS'])
    return g.db_con

# This function gets called when the request is done to close db connection
@app.teardown_appcontext
def close_db(e=None):
    db_con = g.pop('db', None)

    if db_con is not None:
        db_con.close()

@app.route('/dbproj/register/<string:user_type>', methods=['POST'])
def register(user_type):
    logger.info('POST /register')
    payload = request.get_json()

    logger.debug(f'POST /register - payload received: {payload}')
    
    if (validator.user_type(user_type) == False):
        response = {'status': StatusCodes['api_error'], 'results': 'Invalid user type'}
        return response
    
    missing_args = validator.user_register_details(user_type, payload)
    if len(missing_args) != 0:
        response = {'status': StatusCodes['api_error'], 'results': f'Missing arguments: {', '.join(missing_args)}'}
        return response
    
    # add to register
    db.register_user(get_db(), user_type, payload)
    
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