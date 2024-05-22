
from flask import Flask, g, request
import src.db as db
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
    
    # check if user_type is a key in UserDetails (patient, assistant, doctor, nurse)
    flag = 0
    for user in UserDetails.keys():
        if user == user_type:
            flag = 1
            break
    if flag == 0:
        response = {'status': StatusCodes['api_error'], 'results': 'you stich... invalid user type'}
        return response

    missing_args = []
    
    # check inside UserDetails[user_type] if all the keys are in the payload
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