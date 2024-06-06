import datetime
import flask
import jwt
import time
from typing import List, Dict

import src.db as db
import src.validator as validator
from src.utils import logger, STATUS_CODES
from src.api import app, token_required, endpoint_error_handler

#todo: add types to routes

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



@app.route('/dbproj/user', methods=['PUT'])
@endpoint_error_handler
def authenticate_user():
    """
    User Authentication. Login using the username and the password and receive an authentication token (e.g., JSON Web Token (JWT), https://jwt.io/introduction ) in case of success. This token should be included in the header of the remaining requests.
    req PUT http://localhost:8080/dbproj/user {“username”: username, “password”: password}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: auth_token (if it succeeds)}
    """
    #payload logging and validation
    payload = flask.request.get_json()
    logger.info('PUT /dbproj/user')
    logger.debug(f'PUT /dbproj/user - payload received: {payload}')
    validator.user_login_details(payload) # check if payload has username and password

    #authentication logic
    login_id, login_types = db.login_user(flask.g.db_con, payload)
    print("AT AUTHENTICATE:", login_id, login_types)
    try:
        token_payload = {
            'login_id': login_id,
            'login_types': login_types,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'])
    except:
        raise ValueError("Error encoding token")
    
    response = {'status': STATUS_CODES['success'], 'results': token}

    #response logging and return
    logger.debug(f'PUT /dbproj/user - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/register/<user_type>', methods=['POST'])
@endpoint_error_handler
def register(user_type):
    """
    Register User. Create a new user of the specified user_type and return the user_id if successful.
    req POST http://localhost:8080/dbproj/register/patient
    POST http://localhost:8080/dbproj/register/assistant
    POST http://localhost:8080/dbproj/register/nurse
    POST http://localhost:8080/dbproj/register/doctor
    {“username”: username, “email”: email, “password”: password, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: user_id (if it succeeds)}
    """
    #payload logging and validation
    payload = flask.request.get_json()
    logger.info('POST /register')
    logger.debug(f'POST /register - payload received: {payload}')
    validator.user_type(user_type) # check if user_type is valid
    validator.user_register_details(user_type, payload) # check if payload has all the required fields

    #registration logic
    register_id = db.register_user(flask.g.db_con, user_type, payload)
    response = {'status': STATUS_CODES['success'], 'results': register_id}

    #response logging and return
    logger.debug(f'POST /register - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/appointment', methods=['POST'])
@token_required
@endpoint_error_handler
def schedule_appointment(login_id=None, login_types=None):
    """
    Schedule Appointment. Create a new appointment, inserting the data required by the data model. 
    Only a patient can use this endpoint. 
    Remember that for each new appointment a bill should also be created using triggers.
    req POST http://localhost:8080/dbproj/appointment “doctor_id”: doctor_user_id, “date”: date, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”:appointment_id (if it succeeds)}
    """
    #endpoint validation logic
    if 'patient' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)

    #payload logging and validation
    payload = flask.request.get_json()
    logger.info('POST /dbproj/appointment')
    logger.debug(f'POST /dbproj/appointment - payload received: {payload}')
    validator.appointment_details(payload) # check if payload has doctor_id, date and nurses, and if nurses is valid

    #appointment schedule logic
    appointment_id = db.schedule_appointment(flask.g.db_con, payload, patient_id=login_id)
    response = {'status': STATUS_CODES['success'], 'results': appointment_id}
    
    #response logging and return
    logger.debug(f'POST /dbproj/appointment - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/appointments/<int:patient_user_id>', methods=['GET'])
@token_required
@endpoint_error_handler
def get_appointments(patient_user_id, login_id=None, login_types=None):
    """
    See Appointments. List all appointments and respective details (e.g., doctor name) of a specific patient. 
    Only assistants and the target patient can use this endpoint.
    req GET http://localhost:8080/dbproj/appointments/{patient_user_id}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [{“id”:
    appointment1_id, “doctor_id”: doctor_user_id, “date”: date}, ... (if it succeeds)]}
    """
    #endpoint validation logic
    if 'patient' in login_types and str(login_id) != patient_user_id and 'assistant' not in login_types:
        print("AT GET APPOINTMENTS:", login_id, patient_user_id, login_id != patient_user_id)
        response = {'status': STATUS_CODES['api_error'], 'results': 'Patient credentials don\'t match patient id'}
        return flask.jsonify(response) 
    elif 'assistant' not in login_types and 'patient' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)

    #logging
    logger.info('GET /dbproj/appointment')

    #appointment get logic
    appointments: List[Dict] = db.get_user_appointments(flask.g.db_con, patient_user_id) #list of dicts/(appointments)
    response = {'status': STATUS_CODES['success'], 'results': appointments}

    #response logging and return
    logger.debug(f'GET /dbproj/appointment - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/surgery', methods=['POST'])
@app.route('/dbproj/surgery/<hospitalization_id>', methods=['POST'])
@token_required
@endpoint_error_handler
def schedule_surgery(hospitalization_id=None, login_id=None, login_types=None):
    """
    Schedule Surgery. Schedule a new surgery, inserting the data required by the data model. 
    Only assistants can use this endpoint. If hospitalization_id is provided, associate with existing hospitalization,
    otherwise create a new hospitalization. Remember that for each new appointment a bill should also be created 
    (or updated if the hospitalization already exists) using triggers.
    req POST http://localhost:8080/dbproj/surgery
    POST http://localhost:8080/dbproj/surgery/{hospitalization_id}
    {“patient_id”: patient_user_id, “doctor”: doctor_user_id, “nurses”: [[nurse_user_id1, role], [nurse_user_id2, role], (...)], “date”: date, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: {“hospitalization_id”: hospitalization_id, “surgery_id”: surgery_id, “patient_id”: patient_user_id, “doctor_id”: doctor_user_id, “date”: date ... (if it succeeds)}}
    """
    #endpoint validation logic
    if 'assistant' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)
    
    #payload logging and validation
    payload = flask.request.get_json()
    logger.info('POST /dbproj/surgery')
    logger.debug(f'POST /dbproj/surgery - payload received: {payload}')
    validator.surgery_details(payload, hospitalization_id) # check if payload has patient_id, doctor, nurses, date

    #surgery schedule logic
    result: Dict = db.schedule_surgery(flask.g.db_con, payload, hospitalization_id, login_id) #dict with hospitalization, surgery, patient and doctor id, and date
    response = {'status': STATUS_CODES['success'], 'results': result}
    
    #response logging and return
    logger.debug(f'POST /dbproj/surgery - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/prescriptions/<patient_user_id>', methods=['GET'])
@token_required
@endpoint_error_handler
def get_prescriptions(patient_user_id, login_id=None, login_types=None):
    """
    Get Prescriptions. Get the list of prescriptions and respective details for a patient. 
    Only employees or the targeted patient can use this endpoint.
    req GET http://localhost:8080/dbproj/prescriptions/{person_id}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [{“id”:
    presciption_id, “validity”: date “posology”: ["dose”: value, frequency”: frequency, “medicine”: medicine_name]}, {...}] (if it succeeds)}
    """
    #endpoint validation logic
    if 'patient' in login_types and len(login_types) == 1 and str(login_id) != patient_user_id:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Patient credentials don\'t match patient id'}
        return flask.jsonify(response)
    
    #logging
    logger.info(f'GET /dbproj/prescriptions/{patient_user_id}')
 
    #prescription get logic
    prescriptions: List[Dict] = db.get_prescriptions(flask.g.db_con, patient_user_id) #list of dicts/(prescriptions)
    response = {'status': STATUS_CODES['success'], 'results': prescriptions}
    
    #response logging and return
    logger.debug(f'GET /dbproj/appointment - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/prescription/', methods=['POST'])
@token_required
@endpoint_error_handler
def add_prescription(login_id=None, login_types=None):
    """
    Add Prescriptions. When an appointment or hospitalization takes place, a prescription might be necessary. 
    Only doctors can use this endpoint.
    req POST http://localhost:8080/dbproj/prescription/
    {“type”: “hospitalization/appointment”, “event_id”: id, “validity”: date, “medicines”: [{“medicine”: medicine1_name, 
    “posology_dose”: value, “posology_frequency”: value,(...)},
    {“medicine”: medicine2_name, “posology_dose”: value, “posology_frequency”: value, (...)}]}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: prescription_id (...)
          (if it succeeds)}
    """
    # logic to add prescriptions here
    if 'doctor' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)
    
    # payload logging and validation
    payload = flask.request.get_json()
    logger.info('POST /dbproj/prescription')
    logger.debug(f'POST /dbproj/prescription - payload received: {payload}')
    validator.prescription_details(payload) # check for type, event_id, validity and medicines, and if type is valid (prevents SQL injection)

    # prescription creation logic
    prescription_id = db.add_prescription(flask.g.db_con, payload) #prescription id
    response = {'status': STATUS_CODES['success'], 'results': prescription_id}

    # response logging and return
    logger.debug(f'POST /dbproj/prescription - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/bills/<bill_id>', methods=['POST'])
@token_required
@endpoint_error_handler
def execute_payment(bill_id, login_id=None, login_types=None):
    """
    Execute Payment. Pay existing bill. After payment is complete (one bill can have multiple payments) 
    the bill status is updated to “paid”. Only the patient can pay his/her own bills.
    req POST http://localhost:8080/dbproj/bills/{bill_id} {“amount”: value, “payment_method”: value, (...)}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: remaining_value}
    """
    # payment execution logic here
    if 'patient' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)
    
    # payload logging and validation
    payload = flask.request.get_json()
    logger.info(f'POST /dbproj/bills{bill_id}')
    logger.debug(f'POST /dbproj/bills{bill_id} - payload received: {payload}')
    validator.payment_details(payload) # check if payload has amount and payment_method

    # payment execution logic
    remaining_value = db.execute_payment(flask.g.db_con, login_id, bill_id, payload) #remaining value after payment
    response = {'status': STATUS_CODES['success'], 'results': remaining_value}

    # response logging and return
    logger.debug(f'POST /dbproj/bills{bill_id} - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/top3', methods=['GET'])
@token_required
@endpoint_error_handler
def list_top3_patients(login_id=None, login_types=None):
    """
    List Top 3 patients. Get the top 3 patients considering the money spent in the Hospital for the current month. 
    The result should discriminate the respective procedures' details. Use just one SQL query.
    Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/top3
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [
    {“patient_name”: patient1_name, “amount_spent”: value, “procedures”: [{“id”: appointment_id, “doctor_id”: doctor_user_id, “date”: date (...)}]},
    {“patient_name”: patient2_name, “amount_spent”: value, “procedures”: [{“id”: appointment_id, “doctor_id”: doctor_user_id, “date”: date (...)}]},
    ] (if it succeeds)}
    """
    # logic to list top 3 patients here
    if 'assistant' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)
    
    # logging
    logger.info('GET /dbproj/top3')

    # top 3 patients logic
    top3_patients: List[Dict] = db.get_top3_patients(flask.g.db_con) #list of dicts/(patients)
    response = {'status': STATUS_CODES['success'], 'results': top3_patients}

    # response logging and return
    logger.debug(f'GET /dbproj/top3 - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/daily/<int:year>-<int:month>-<int:day>', methods=['GET'])
@token_required
@endpoint_error_handler
def daily_summary(year, month, day, login_id=None, login_types=None):
    """
    Daily Summary. List a count for all hospitalizations details of a given day. Consider, surgeries, 
    payments, and prescriptions. Just one SQL query should be used to obtain the information. 
    Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/daily/{year-month-day}
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: {“amount_spent”:
    value, “surgeries”: count, “prescriptions”: count}}
    """
    # logic to get daily summary here
    if 'assistant' not in login_types:
        response = {'status': STATUS_CODES['api_error'], 'results': 'Invalid credentials to access this endpoint'}
        return flask.jsonify(response)
    
    # logging
    logger.info(f'GET /dbproj/daily{year}-{month}-{day}')

    # daily summary logic
    date = f'{year}-{month:02d}-{day:02d}' 
    daily_summary: Dict = db.get_daily_summary(flask.g.db_con, date)
    response = {'status': STATUS_CODES['success'], 'results': daily_summary}

    # response logging and return
    logger.debug(f'GET /dbproj/daily{date} - response: {response}')
    return flask.jsonify(response)



@app.route('/dbproj/report', methods=['GET'])
@token_required
@endpoint_error_handler
def generate_monthly_report(login_id=None, login_types=None):
    """
    Generate a monthly report. Get a list of the doctors with more surgeries each month in the last 12 months.
    Just one SQL query should be used to obtain the information. Only assistants can use this endpoint.
    req GET http://localhost:8080/dbproj/report
    res {“status”: status_code, “errors”: errors (if any occurs), “results”: [
    {“month”: “month_0”, “doctor”: name, “surgeries”: total_surgeries}, {“month”: “month_1”, “doctor”: name, “surgeries”: total_surgeries}, {“month”: “month_2”, “doctor”: name, “surgeries”: total_surgeries},
    (...) ]}
    """
    # logging
    logger.info('GET /dbproj/report')

    # monthly report logic
    monthly_report: List[Dict] = db.generate_monthly_report(flask.g.db_con)
    response = {'status': STATUS_CODES['success'], 'results': monthly_report}

    # response logging and return
    logger.debug(f'GET /dbproj/report - response: {response}')
    return flask.jsonify(response)