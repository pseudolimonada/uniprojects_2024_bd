
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
    """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """
    return """
    Hello from Unicorn Hospital <br/>
    <br/>
    BD 2023-2024<br/>
    <br/>
    """
# get.db guarda a coexão
#payload ´r



@app.route('/dbproj/user', methods=['PUT'])
def authenticate_user():
    """
    User Authentication. Login using the username and the password and receive an authentication token (e.g., JSON Web Token (JWT), https://jwt.io/introduction ) in case of success. This token should be included in the header of the remaining requests.
    req PUT http://localhost:8080/dbproj/user {“username”: username, “password”: password}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: auth_token (if it succeeds)}
    """
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
    """
    Register User. Create a new user of the specified user_type and return the user_id if successful.
    req POST http://localhost:8080/dbproj/register/patient
    POST http://localhost:8080/dbproj/register/assistant
    POST http://localhost:8080/dbproj/register/nurse
    POST http://localhost:8080/dbproj/register/doctor
    {“username”: username, “email”: email, “password”: password, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: user_id (if it succeeds)}
    """

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
    """
    Schedule Appointment. Create a new appointment, inserting the data required by the data model. Only a patient can use this endpoint. Remember that for each new appointment a bill should also be created using triggers.
    req POST http://localhost:8080/dbproj/appointment “doctor_id”: doctor_user_id, “date”: date, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”:appointment_id (if it succeeds)}
    """
    # appointment scheduling logic here
    payload = flask.request.get_json()
    logger.info('POST /appointment')
    logger.debug(f'POST /appointment - payload received: {payload}')

    try:
        validator.user_type()

    pass


@app.route('/dbproj/appointments/<patient_user_id>', methods=['GET'])
@token_required
def see_appointments(login_id=None, login_types=None):
    """
    See Appointments. List all appointments and respective details (e.g., doctor name) of a specific patient Only assistants and the target patient can use this endpoint.
    req GET http://localhost:8080/dbproj/appointments/{patient_user_id}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [{“id”:
    appointment1_id, “doctor_id”: doctor_user_id, “date”: date}, ... (if it succeeds)]}
    """
    # logic to list all appointments here
    pass



@app.route('/dbproj/surgery', methods=['POST'])
@app.route('/dbproj/surgery/<hospitalization_id>', methods=['POST'])
@token_required
def schedule_surgery(hospitalization_id=None, login_id=None, login_types=None):
    """
    Schedule Surgery. Schedule a new surgery, inserting the data required by the data model. Only assistants can use this endpoint. If hospitalization_id is provided, associate with existing hospitalization, otherwise create a new hospitalization. Remember that for each new appointment a bill should also be created (or updated if the hospitalization already exists) using triggers.
    req POST http://localhost:8080/dbproj/surgery
    POST http://localhost:8080/dbproj/surgery/{hospitalization_id}
    {“patient_id”: patient_user_id, “doctor”: doctor_user_id, “nurses”: [[nurse_user_id1, role], [nurse_user_id2, role], (...)], “date”: date, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: {“hospitalization_id”: hospitalization_id, “surgery_id”: surgery_id, “patient_id”: patient_user_id, “doctor_id”: doctor_user_id, “date”: date ... (if it succeeds)}}
    """
    # surgery scheduling logic here
    pass



@app.route('/dbproj/prescriptions/<person_id>', methods=['GET'])
@token_required
def get_prescriptions(login_id=None, login_types=None):
    """
    Get Prescriptions. Get the list of prescriptions and respective details for a patient. Only employees or the targeted patient can use this endpoint.
    req GET http://localhost:8080/dbproj/prescriptions/{person_id}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [{“id”:
    presciption_id, “validity”: date “posology”: ["dose”: value, frequency”: frequency, “medicine”: medicine_name]}, {...}] (if it succeeds)}
    """
    # logic to get prescriptions here
    pass



@app.route('/dbproj/prescription/', methods=['POST'])
@token_required
def add_prescriptions(login_id=None, login_types=None):
    """
    Add Prescriptions. When an appointment or hospitalization takes place, a prescription might be necessary. Only doctors can use this endpoint.
    req POST http://localhost:8080/dbproj/prescription/
    {“type”: “hospitalization/appointment”, “event_id”: id, “validity”: date, “medicines”: [{“medicine”: medicine1_name, “posology_dose”: value, “posology_frequency”: value,
                   Page 6 of 7
    (...)},{“medicine”: medicine2_name, “posology_dose”: value, “posology_frequency”: value,
    (...)}]}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: prescription_id (...)
          (if it succeeds)}
    """
    # logic to add prescriptions here
    pass



@app.route('/dbproj/bills/<bill_id>', methods=['POST'])
@token_required
def execute_payment(bill_id, login_id=None, login_types=None):
    """
    Execute Payment. Pay existing bill. After payment is complete (one bill can have multiple payments) the bill status is updated to “paid”. Only the patient can pay his/her own bills.
    req POST http://localhost:8080/dbproj/bills/{bill_id} {“amount”: value, “payment_method”: value, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: remaining_value}
    """
    # payment execution logic here
    pass



@app.route('/dbproj/top3', methods=['GET'])
@token_required
def list_top3_patients(login_id=None, login_types=None):
    """
    List Top 3 patients. Get the top 3 patients considering the money spent in the Hospital for the current month. The result should discriminate the respective procedures’ details. Just one SQL query should be used to obtain the information. Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/top3
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [
    {“patient_name”: patient1_name, “amount_spent”: value, “procedures”: [{“id”: appointment_id, “doctor_id”: doctor_user_id, “date”: date (...)}]},
    {“patient_name”: patient2_name, “amount_spent”: value, “procedures”: [{“id”: appointment_id, “doctor_id”: doctor_user_id, “date”: date (...)}]},
    ] (if it succeeds)}
    """
    # logic to list top 3 patients here
    pass



@app.route('/dbproj/daily/<date>', methods=['GET'])
@token_required
def daily_summary(date, login_id=None, login_types=None):
    """
    Daily Summary. List a count for all hospitalizations details of a given day. Consider, surgeries, payments, and prescriptions. Just one SQL query should be used to obtain the information. Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/daily/{year-month-day}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: {“amount_spent”:
    value, “surgeries”: count, “prescriptions”: count}}
    """
    # logic to get daily summary here
    pass



@app.route('/dbproj/report', methods=['GET'])
@token_required
def generate_monthly_report(login_id=None, login_types=None):
    """
    Generate a monthly report. Get a list of the doctors with more surgeries each month in the last 12 months. Just one SQL query should be used to obtain the information. Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/report
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [
    {“month”: “month_0”, “doctor”: name, “surgeries”: total_surgeries}, {“month”: “month_1”, “doctor”: name, “surgeries”: total_surgeries}, {“month”: “month_2”, “doctor”: name, “surgeries”: total_surgeries},
    (...) ]}
    """
    # logic to generate monthly report here
    pass