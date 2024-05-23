import psycopg2
import sys
from psycopg2 import pool
from src.utils import config, logger

from typing import List, Dict

# creates a pool of connections to the database (being opened/closed implicitly in all endpoints, setup in api.py)
db_pool = pool.SimpleConnectionPool(
    1, 20,
    user=config['DB_USER'], password=config['DB_PASS'],
    host=config['DB_HOST'], port=config['DB_PORT'],
    database=config['DB_NAME'])


def _execute_query(db_con, query, values=None, fetch_id=False, commit=True):   #careful that values must be a tuple even if it's a single value
    cursor = db_con.cursor()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    if fetch_id:
        return cursor.fetchone()[0] # might raise errors if empty
    if commit:
        db_con.commit()
    cursor.close()

def _build_insert_query(table_name, field_list, fetch=None):
    columns = ', '.join(field_list)
    values = ', '.join(['%s'] * len(field_list))
    query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({values})"""
    if fetch:
        query += f" RETURNING {fetch}"
    return query

# PROTOTYPICAL QUERY
# query = """"
#     SOMETHING SOMETHING
#     SOMETHING SOMETHING %s
#     SOMETHING %s SOMETHING """
# values = (
#     variable1,
#     variable2)
# _execute_query(db_con, query, values)

def register_user(db_con, user_type, payload):
    #todo: check if user already exists (nvm the unique constrainti in db fixes)
    person_field_list = ["username", "password", "name", "address", "cc_number", "nif_number", "birth_date"]

    # password hashing (could also salt it, hash the salt, salt the hash...)
    hashed_password = hash(payload['password'])
    payload['password'] = hashed_password

    query = _build_insert_query('person',person_field_list, fetch='id')
    values = tuple([payload[field] for field in person_field_list])

    user_id = _execute_query(db_con, query, values, fetch_one=True, commit=False)[0] #returns user row as list, [0] for id

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

def login_user(db_con, payload):
    # Query to check for username and password in the person table
    query = """
    SELECT id FROM person WHERE username = %s AND password = %s
    """
    values = (payload['username'], hash(payload['password']))
    cursor = db_con.cursor()
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
    SELECT 'patient' FROM patient WHERE employee_person_id = %s
    """
    values = (login_id, login_id, login_id, login_id)
    (query, values)

    login_types = [row[0] for row in cursor.fetchall()] # builds list of user roles

    cursor.close()
    
    if len(login_types) == 0:
        raise ValueError('User has no roles assigned')

    return login_id, login_types

def check_user(db_con, user_id, user_type=None):
    if user_type is None:
        query = """
        SELECT 1 FROM person WHERE id = %s
        """
    else:
        query = f"""
        SELECT 1 FROM {user_type} WHERE employee_person_id = %s
        """
    values = (user_id,) # tuple with a single element, requirement of the execute method

    cursor = db_con.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise ValueError(f'User is not a {user_type}')


def schedule_appointment(db_con, payload, patient_id) -> int:
    pass

def get_user_appointments(db_con, patient_user_id) -> List[Dict]:
    pass

def schedule_surgery(db_con, payload, hospitalization_id) -> Dict:
    if hospitalization_id is None:
        #create hospitalization
        pass
    #schedule surgery
    pass

def get_prescriptions(db_con, patient_id) -> List[Dict]:
    pass

def add_prescription(db_con, payload) -> int:
    pass

def execute_payment(db_con, bill_id, payload):
    pass

def get_top3_patients(db_con):
    pass

def get_daily_summary(db_con, date):
    pass

def generate_monthly_report(db_con):
    pass

