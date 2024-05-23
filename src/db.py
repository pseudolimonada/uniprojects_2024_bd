import psycopg2
from psycopg2 import pool
from src.utils import config

# creates a pool of connections to the database
db_pool = pool.SimpleConnectionPool(
    1, 20,
    user=config['DB_USER'], password=config['DB_PASS'],
    host=config['DB_HOST'], port=config['DB_PORT'],
    database=config['DB_NAME'])


# INNER FUNCTIONS


def _execute_query(db_con, query, values=None, fetch_id=False):   #careful that values must be a tuple even if it's a single value
    cursor = db_con.cursor()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    db_con.commit()
    if fetch_id:
        return cursor.fetchone()[0] # might raise errors if empty
    cursor.close()

def _build_insert_query(table_name, field_list):
    columns = ', '.join(field_list)
    values = ', '.join(['%s'] * len(field_list))
    query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({values})"""
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
    person_field_list = ["username", "password", "name", "address", "cc_number", "nif_number", "birth_date"]

    # password hashing (could also salt it, hash the salt, salt the hash...)
    hashed_password = hash(payload['password'])
    payload['password'] = hashed_password

    query = _build_insert_query('person',person_field_list)
    values = tuple([payload[field] for field in person_field_list])
    user_id = _execute_query(db_con, query, values, fetch_id=True)

    if user_type == 'patient':
        register_patient(db_con, user_id, payload)
    else:
        register_employee(db_con, user_type, user_id, payload)
    
    return user_id


def register_patient(db_con, user_id, payload):
    query = _build_insert_query('patient', ['medical_history', 'person_id'])
    values = (user_id, payload['medical_history'])
    _execute_query(db_con, query, values)


def register_employee(db_con, user_type, user_id, payload):
    query = _build_insert_query('employee', ['contract_details', 'person_id'])
    values = (user_id, payload['contract_details'])
    _execute_query(db_con, query, values)

    if user_type == 'doctor':
        register_doctor(db_con, user_id, payload)


def register_doctor(db_con, user_id, payload):
    query = """
    INSERT INTO doctor (license, specialization_id, person_employee_id)
    VALUES (%s, (SELECT id FROM specialization WHERE name = %s), %s)
    """
    values = (payload['license'], payload['specialization'], user_id)
    _execute_query(db_con, query, values)


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

    user_id = result[0]

    # Single query to check for the user_id in the doctor, nurse, assistant, and patient tables efficiently
    query = """
    SELECT 'doctor' AS user_type FROM doctor WHERE person_employee_id = %s
    UNION ALL
    SELECT 'nurse' FROM nurse WHERE person_employee_id = %s
    UNION ALL
    SELECT 'assistant' FROM assistant WHERE person_employee_id = %s
    UNION ALL
    SELECT 'patient' FROM patient WHERE person_employee_id = %s
    """
    values = (user_id, user_id, user_id, user_id)
    cursor.execute(query, values)

    user_roles = [row[0] for row in cursor.fetchall()] # builds list of user roles

    cursor.close()
    
    if len(user_roles) == 0:
        raise ValueError('User has no roles assigned')

    return user_id, user_roles

def check_user(db_con, user_id, user_type=None):
    if user_type is None:
        query = """
        SELECT 1 FROM person WHERE id = %s
        """
        values = (user_id,)
    else:
        query = f"""
        SELECT 1 FROM {user_type} WHERE person_employee_id = %s
        """
    values = (user_id,) # tuple with a single element, requirement of the execute method

    cursor = db_con.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise ValueError(f'User is not a {user_type}')

def get_top3_patients(db_con):
    pass

