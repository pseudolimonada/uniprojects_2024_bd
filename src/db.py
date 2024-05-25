import sys
import hashlib
import datetime

import psycopg2
from psycopg2 import pool
from typing import List, Dict

from src.utils import config, logger, get_date_from_dateobj, get_timestamp_from_dateobj, get_dateobj_from_date, get_dateobj_from_timestamp

# creates a pool of connections to the database (being opened/closed implicitly in all endpoints, setup in api.py)
db_pool = pool.SimpleConnectionPool(
    1, 20,
    user=config['DB_USER'], password=config['DB_PASS'],
    host=config['DB_HOST'], port=config['DB_PORT'],
    database=config['DB_NAME'])


def _execute_query(db_con, query, values=None, fetch_id=False, commit=True):  # careful that values must be a tuple even if it's a single value
    with db_con.cursor() as cursor:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        if fetch_id:
            return cursor.fetchone() #returns empty lisit if empty
        if commit:
            db_con.commit()


def _build_insert_query(table_name, field_list, fetch=None):
    columns = ', '.join(field_list)
    values = ', '.join(['%s'] * len(field_list))
    query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({values})"""
    if fetch:
        query += f" RETURNING {fetch}"
    return query


# PROTOTYPICAL SIMPLE QUERY
# query = """"
#     SOMETHING SOMETHING
#     SOMETHING SOMETHING %s
#     SOMETHING %s SOMETHING """
# values = (
#     variable1,
#     variable2)
# _execute_query(db_con, query, values)


def login_user(db_con, payload):
    # Query to check for username and password in the person table
    query = """
    SELECT id FROM person WHERE username = %s AND password = %s
    """
    print(payload['username'], payload['password'])
    values = (payload['username'], hashlib.sha256(payload['password'].encode()).hexdigest())
    
    with db_con.cursor() as cursor:
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result is None:
            raise ValueError('Invalid username or password')

        login_id = result[0]

        # Single query to check for the user_id in the doctor, nurse, assistant, and patient tables efficiently
        query = """
        SELECT 'doctor' AS user_type FROM doctor WHERE employee_person_id = %s
        UNION ALL
        SELECT 'nurse' FROM nurse WHERE employee_person_id = %s
        UNION ALL
        SELECT 'assistant' FROM assistant WHERE employee_person_id = %s
        UNION ALL
        SELECT 'patient' FROM patient WHERE person_id = %s
        """
        values = (login_id, login_id, login_id, login_id)
        cursor.execute(query, values)

        login_types = [row[0] for row in cursor.fetchall()]  # builds list of user roles

    if len(login_types) == 0:
        raise ValueError('User has no roles assigned')

    return login_id, login_types

def check_user(db_con, user_id, user_type=None):
    if user_type is None:
        query = """
        SELECT id FROM person WHERE id = %s
        """
        values = (user_id,)
    else:
        query = f"""
        SELECT id FROM {user_type} WHERE employee_person_id = %s
        """
    values = (user_id,)  # tuple with a single element, requirement of the execute method

    with db_con.cursor() as cursor:
        cursor.execute(query, values)
        result = cursor.fetchone()

    if result is None:
        raise ValueError(f'User is not a {user_type}')

    return result[0]

def register_user(db_con, user_type, payload):
    # todo: check if user already exists (nvm the unique constrainti in db fixes)
    person_field_list = ["username", "password", "name", "address", "cc_number", "nif_number", "birth_date"]

    # password hashing (could also salt it, hash the salt, salt the hash...)
    hashed_password = hashlib.sha256(payload['password'].encode()).hexdigest()
    payload['password'] = hashed_password

    query = _build_insert_query('person', person_field_list, fetch='id')
    values = tuple([payload[field] for field in person_field_list])

    user = _execute_query(db_con, query, values, fetch_id=True, commit=False)

    if user is None:
        raise ValueError('Error creating user')
    
    user_id = user[0]

    logger.debug(f"User ID: {user_id}")

    if user_type == 'patient':
        logger.info('Registering patient')
        _register_patient(db_con, user_id, payload)
    else:
        logger.info('Registering employee')
        _register_employee(db_con, user_type, user_id, payload)

    db_con.commit()

    return user_id

def _register_patient(db_con, user_id, payload):
    query = _build_insert_query('patient', ['medical_history', 'person_id'])
    values = (payload['medical_history'], user_id)
    _execute_query(db_con, query, values, commit=False)

def _register_employee(db_con, user_type, user_id, payload):
    query = _build_insert_query('employee', ['contract_details', 'person_id'])
    values = (payload['contract_details'], user_id)
    _execute_query(db_con, query, values, commit=False)

    if user_type == 'doctor':
        _register_doctor(db_con, user_id, payload)
    elif user_type == 'nurse':
        _register_nurse(db_con, user_id, payload)
    elif user_type == 'assistant':
        _register_assistant(db_con, user_id, payload)

def _register_doctor(db_con, user_id, payload):
    query = """
    INSERT INTO doctor (license, specialization_id, employee_person_id)
    VALUES (%s, (SELECT id FROM specialization WHERE name = %s), %s)
    """
    values = (payload['license'], payload['specialization_name'], user_id)

    _execute_query(db_con, query, values, commit=False)

def _register_nurse(db_con, user_id, payload):
    query = _build_insert_query('nurse', ['employee_person_id'])
    values = (user_id,)

    _execute_query(db_con, query, values, commit=False)

def _register_assistant(db_con, user_id, payload):
    query = _build_insert_query('assistant', ['certification_details', 'employee_person_id'])
    values = (payload['certification_details'], user_id)

    _execute_query(db_con, query, values, commit=False)


def get_user_appointments(db_con, patient_user_id) -> List[Dict]:
    pass


# to be tested
def _check_nurses(db_con, nurse_ids, start_date, end_date):
    with db_con.cursor() as cursor:
        # Prepare the nurse IDs for the IN operator
        nurse_ids_tuple = tuple(nurse_ids)

        query = """
            SELECT employee_person_id
            FROM nurse
            WHERE employee_person_id IN %s
            AND employee_person_id NOT IN (
            
                SELECT DISTINCT na.nurse_employee_person_id
                FROM nurse_appointment na
                JOIN appointment a ON na.appointment_event_id = a.event_id
                JOIN event e ON a.event_id = e.id
                WHERE e.start_date < %s AND e.end_date > %s

                UNION ALL

                SELECT DISTINCT ns.nurse_employee_person_id
                FROM nurse_surgery ns
                JOIN surgery s ON ns.surgery_id = s.id
                WHERE s.start_date < %s AND s.end_date > %s

                UNION ALL

                SELECT DISTINCT h.nurse_employee_person_id
                FROM hospitalization h
                JOIN event e ON h.event_id = e.id
                WHERE e.start_date < %s AND e.end_date > %s

                UNION ALL

                SELECT DISTINCT e.patient_person_id
                FROM event e
                WHERE e.start_date < %s AND e.end_date > %s
            )
            LIMIT %s;
            """
        values = (nurse_ids_tuple, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date, len(nurse_ids))
        # Execute the query
        cursor.execute(query, values)
        free_nurses = cursor.fetchall()

        if len(free_nurses) < len(nurse_ids):
            raise ValueError('Not enough nurses available for the given date')
  
        return nurse_ids

def _check_doctor(db_con, doctor_id , start_date, end_date):
    # Retrieve an available doctor
    query = """
    SELECT d.employee_person_id
    FROM doctor d
    WHERE d.employee_person_id = %s
    AND d.employee_person_id NOT IN (
        SELECT DISTINCT a.doctor_employee_person_id
        FROM appointment a
        JOIN event e ON a.event_id = e.id
        WHERE e.start_date < %s AND e.end_date > %s

        UNION ALL

        SELECT DISTINCT s.doctor_employee_person_id
        FROM surgery s
        JOIN event e ON s.hospitalization_event_id = e.id
        WHERE e.start_date < %s AND e.end_date > %s

        UNION ALL

        SELECT DISTINCT e.patient_person_id
        FROM event e
        WHERE e.start_date < %s AND e.end_date > %s
    )
    LIMIT 1;
    """
    values = (doctor_id, end_date, start_date, end_date, start_date, end_date, start_date)
    doctor = _execute_query(db_con, query, values, fetch_id=True)

    if doctor is None:
        raise ValueError(f'Doctor is not available for the given date')

    return doctor

def _check_patient(db_con, patient_id, start_date, end_date):
    # Retrieve an available patient
    query = """
    SELECT p.person_id
    FROM patient p
    WHERE p.person_id = %s
    AND p.person_id  NOT IN (
        SELECT DISTINCT e.patient_person_id
        FROM event e
        WHERE e.start_date < %s AND e.end_date > %s
    )
    LIMIT 1;
    """
    values = (patient_id, end_date, start_date)
    patient = _execute_query(db_con, query, values, fetch_id=True)

    if patient is None:
        raise ValueError(f'Patient is not available for the given date')

    return patient[0]

def schedule_appointment(db_con, payload, patient_id) -> int:
    start_date = get_dateobj_from_timestamp(payload['date'])
    end_date = start_date + datetime.timedelta(hours=1)

    if start_date < datetime.datetime.now():
        raise ValueError('Stop there time traveler')

    doctor_id = payload['doctor_id']
    nurses:List[List] = payload['nurses']
    nurse_ids = [nurse[0] for nurse in nurses]

    if patient_id in nurse_ids or patient_id == doctor_id:
        raise ValueError('Cannot schedule an appointment with yourself')

    free_doctor = _check_doctor(db_con, doctor_id, start_date, end_date)
    free_nurses = _check_nurses(db_con, nurse_ids, start_date, end_date)
    free_patient = _check_patient(db_con, patient_id, start_date, end_date)

    # Create appointment
    event = _create_appointment(db_con, start_date, end_date, patient_id, doctor_id , nurses)

    if event is None:
        raise ValueError('Error scheduling appointment')

    return event[0]

def _create_appointment(db_con, start_date, end_date, patient_id, doctor_id, nurses):
    with db_con.cursor() as cursor:
        cursor.execute(
            "INSERT INTO event (start_date, end_date, patient_person_id) VALUES (%s, %s, %s) RETURNING id",
            (start_date, end_date, patient_id)
        )
        event = cursor.fetchone()

        # Insert the new appointment
        cursor.execute(
            "INSERT INTO appointment (event_id, doctor_employee_person_id) VALUES (%s, %s)",
            (event, doctor_id)
        )

        data = [(event, nurse[0], nurse[1]) for nurse in nurses]
        # Insert the new nurse appointments
        cursor.executemany(
            "INSERT INTO nurse_appointment (appointment_event_id, nurse_employee_person_id, role) VALUES (%s, %s, %s)",
            data
        )

        db_con.commit() # commit the transaction

    if event is None:
        raise ValueError('Error creating event')
    
    return event

def schedule_surgery(db_con, payload, hospitalization_id, login_id) -> Dict:
    start_date = get_dateobj_from_timestamp(payload['date'])
    end_date = start_date + datetime.timedelta(hours=1)
    patient_id = payload['patient_id'] 

    if patient_id == login_id:
        raise ValueError('Cannot schedule surgery for yourself')

    if start_date < datetime.datetime.now():
        raise ValueError('Stop there time traveler!')
    
    if hospitalization_id is None:
        end_date_hosp = start_date + datetime.timedelta(days=payload['hospitalization_duration'])
        hospitalization_nurse_id = payload['hospitalization_nurse_id']

        event = _create_hospitalization(
            db_con, start_date, end_date_hosp, patient_id, hospitalization_nurse_id)
        
        if event is None:
            raise ValueError('Error creating hospitalization')
        
        hospitalization_id = event[0]

    doctor_id = payload['doctor_id']
    nurses:List[List] = payload['nurses']
    nurse_ids = [nurse[0] for nurse in nurses]

    # create surgery
    free_nurses = _check_nurses(db_con, nurse_ids, start_date, end_date)
    free_doctor = _check_doctor(db_con, doctor_id, start_date, end_date)
    free_patient = _check_patient(db_con, patient_id, start_date, end_date)

    surgery = _create_surgery(
        db_con, start_date, end_date, patient_id, doctor_id, nurses, hospitalization_id)

    if surgery is None:
        raise ValueError('Error scheduling surgery')
    
    return hospitalization_id, surgery[0]

def _create_hospitalization(db_con, start_date, end_date, patient_id, nurse_id):
    with db_con.cursor() as cursor:
        cursor.execute(
            "INSERT INTO event (start_date, end_date, patient_person_id) VALUES (%s, %s, %s) RETURNING id",
            (start_date, end_date, patient_id)
        )

        event = cursor.fetchone()

        cursor.execute(
            "INSERT INTO hospitalization (event_id, nurse_employee_person_id) VALUES (%s, %s)",
            (event, nurse_id)
        )

        db_con.commit()

    if event is None:
        raise ValueError('Error creating event')
    
    return event

def _create_surgery(db_con, start_date, end_date, patient_id, doctor_id, nurses, hospitalization_id):
    pass


def get_prescriptions(db_con, patient_id) -> List[Dict]:
    pass


def add_prescription(db_con, payload) -> int:
    pass


def execute_payment(db_con, login_id, bill_id, payload):
    pass


def get_top3_patients(db_con):
    pass


def get_daily_summary(db_con, date):
    pass


def generate_monthly_report(db_con):
    pass

