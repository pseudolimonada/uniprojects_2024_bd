import sys
import hashlib
import datetime
import calendar

import psycopg2
from psycopg2 import pool
from typing import List, Dict

from src.utils import config, logger, get_dateobj_from_timestamp, get_dateobj_from_date

# creates a pool of connections to the database (being opened/closed implicitly in all endpoints, setup in api.py)
db_pool = pool.SimpleConnectionPool(
    1, 20,
    user=config['DB_USER'], password=config['DB_PASS'],
    host=config['DB_HOST'], port=config['DB_PORT'],
    database=config['DB_NAME'])

# wrapper to open/close cursor and commit/rollback transactions
def transactional(func):
    def wrapper(*args, **kwargs):
        db_con = args[0]
        with db_con.cursor() as cursor:
            try:
                db_con.autocommit = False
                result = func(*args, **kwargs, cursor=cursor)
            except Exception as e:
                db_con.rollback()
                logger.error(f"Error in transaction: {str(e)}")
                raise
            else:
                db_con.commit()
                return result
            finally:
                db_con.autocommit = True
    return wrapper

# util function to build an simple insert query with a list of fields
def _build_insert_query(table_name, field_list, fetch=None):
    columns = ', '.join(field_list)
    values = ', '.join(['%s'] * len(field_list))
    query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({values}) 
        """
    if fetch:
        query += f" RETURNING {fetch}"
    return query

@transactional
def login_user(db_con, payload, cursor=None):
    # Query to check for username and password in the person table
    query = """
    SELECT id FROM person WHERE username = %s AND password = %s
    """
    print(payload['username'], payload['password'])
    values = (payload['username'], hashlib.sha256(payload['password'].encode()).hexdigest())
    
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
        raise ValueError('User hasn\'t been assigned a role')

    return login_id, login_types

@transactional
def check_user_from_token(db_con, user_id, user_type=None, cursor=None):
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

    cursor.execute(query, values)
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f'User is not a {user_type}')

    return result[0]

@transactional
def register_user(db_con, user_type, payload, cursor=None) -> int:
    person_field_list = ["username", "password", "name", "address", "cc_number", "nif_number", "birth_date"]

    # password hashing (could also salt it, hash the salt, salt the hash...)
    hashed_password = hashlib.sha256(payload['password'].encode()).hexdigest()
    payload['password'] = hashed_password

    query = _build_insert_query('person', person_field_list, fetch='id')
    values = tuple([payload[field] for field in person_field_list])

    cursor.execute(query, values)
    user = cursor.fetchone()

    if user is None:
        raise ValueError('Error creating user')
    
    user_id = user[0]

    logger.debug(f"User ID: {user_id}")

    if user_type == 'patient':
        logger.info('Registering patient')
        _register_patient(user_id, payload, cursor=cursor)
    else:
        logger.info('Registering employee')
        _register_employee(user_type, user_id, payload, cursor=cursor)

    return {
        "user_id": user_id,
        "user_type": user_type
    }

def _register_patient(user_id, payload, cursor=None):
    query = _build_insert_query('patient', ['medical_history', 'person_id'])
    values = (payload['medical_history'], user_id)

    cursor.execute(query, values)

def _register_employee(user_type, user_id, payload, cursor=None):
    query = _build_insert_query('employee', ['contract_details', 'person_id'])
    values = (payload['contract_details'], user_id)

    cursor.execute(query, values)

    if user_type == 'doctor':
        _register_doctor(user_id, payload, cursor=cursor)
    elif user_type == 'nurse':
        _register_nurse(user_id, payload, cursor=cursor)
    elif user_type == 'assistant':
        _register_assistant(user_id, payload,cursor=cursor)

def _register_doctor(user_id, payload, cursor=None):
    query = """
    INSERT INTO doctor (license, specialization_id, employee_person_id)
    VALUES (%s, (SELECT id FROM specialization WHERE name = %s), %s)
    """
    values = (payload['license'], payload['specialization_name'], user_id)

    cursor.execute(query, values)

def _register_nurse(user_id, payload, cursor=None):
    query = _build_insert_query('nurse', ['employee_person_id'])
    values = (user_id,)

    cursor.execute(query, values)

def _register_assistant(user_id, payload, cursor=None):
    query = _build_insert_query('assistant', ['certification_details', 'employee_person_id'])
    values = (payload['certification_details'], user_id)

    cursor.execute(query, values)

@transactional
def get_user_appointments(db_con, patient_user_id, cursor=None) -> List[Dict]:
    query = """
    SELECT DISTINCT 
        e.id,
        d.employee_person_id,
        p.name,
        TO_CHAR(e.start_date, 'YYYY-MM-DD HH24:MI')
    FROM event e
    JOIN appointment a ON e.id = a.event_id
    JOIN doctor d ON a.doctor_employee_person_id = d.employee_person_id
    JOIN person p ON p.id = d.employee_person_id
    WHERE e.patient_person_id = %s
    """
    values = (patient_user_id,)

    cursor.execute(query, values)
    appointments = cursor.fetchall()

    if appointments is None:
        raise ValueError("Patient does not have any appointments")
    
    return [{
        "appointment_id": appointment[0],
        "doctor_id": appointment[1],
        "doctor_name": appointment[2],
        "date": appointment[3],
    } for appointment in appointments]

def _check_nurses(nurse_ids, start_date, end_date, cursor=None):
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

    cursor.execute(query, values)
    free_nurses = cursor.fetchall()

    if len(free_nurses) < len(nurse_ids):
        raise ValueError('Not enough nurses available for the given date')

    return [nurse[0] for nurse in free_nurses]

def _check_doctor(doctor_id , start_date, end_date, cursor=None):
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
        WHERE s.start_date < %s AND s.end_date > %s

        UNION ALL

        SELECT DISTINCT e.patient_person_id
        FROM event e
        WHERE e.start_date < %s AND e.end_date > %s
    )
    LIMIT 1;
    """
    values = (doctor_id, end_date, start_date, end_date, start_date, end_date, start_date)
    cursor.execute(query, values)
    doctor = cursor.fetchone()

    if doctor is None:
        raise ValueError(f'Doctor is not available for the given date')

    return doctor[0]

def _check_patient(patient_id, start_date, end_date, cursor=None):
    # Retrieve an available patient
    query = """
    SELECT p.person_id
    FROM patient p
    WHERE p.person_id = %s
    AND p.person_id  NOT IN (
        SELECT DISTINCT e.patient_person_id
        FROM event e
        JOIN appointment a ON e.id = a.event_id
        WHERE e.start_date < %s AND e.end_date > %s

        UNION ALL

        SELECT DISTINCT e.patient_person_id
        FROM event e
        JOIN surgery s ON e.id = s.hospitalization_event_id
        WHERE s.start_date < %s AND s.end_date > %s

        UNION ALL

        SELECT DISTINCT a.doctor_employee_person_id
        FROM appointment a
        JOIN event e ON a.event_id = e.id
        WHERE e.start_date < %s AND e.end_date > %s

        UNION ALL

        SELECT DISTINCT s.doctor_employee_person_id
        FROM surgery s
        WHERE s.start_date < %s AND s.end_date > %s

        UNION ALL

        SELECT DISTINCT ns.nurse_employee_person_id
        FROM nurse_surgery ns
        JOIN surgery s ON ns.surgery_id = s.id
        WHERE s.start_date < %s AND s.end_date > %s

        UNION ALL

        SELECT DISTINCT na.nurse_employee_person_id
        FROM nurse_appointment na
        JOIN appointment a ON na.appointment_event_id = a.event_id
        JOIN event e ON a.event_id = e.id
        WHERE e.start_date < %s AND e.end_date > %s

        UNION ALL

        SELECT DISTINCT h.nurse_employee_person_id
        FROM hospitalization h
        JOIN event e ON h.event_id = e.id
        WHERE e.start_date < %s AND e.end_date > %s
    )
    LIMIT 1;
    """
    values = (patient_id, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date)
    cursor.execute(query, values)
    patient = cursor.fetchone()

    if patient is None:
        raise ValueError(f'Patient is not available for the given date')

    return patient[0]

@transactional
def schedule_appointment(db_con, payload, patient_id, cursor=None) -> int:
    start_date = get_dateobj_from_timestamp(payload['date'])
    end_date = start_date + datetime.timedelta(hours=1)

    if start_date < datetime.datetime.now():
        raise ValueError('Stop there time traveler')

    doctor_id = payload['doctor_id']
    nurses:List[List] = payload['nurses']
    nurse_ids = [nurse[0] for nurse in nurses]

    if patient_id in nurse_ids or patient_id == doctor_id:
        raise ValueError('Cannot schedule an appointment with yourself')

    doctor_id = _check_doctor(doctor_id, start_date, end_date, cursor=cursor)
    nurse_ids = _check_nurses(nurse_ids, start_date, end_date, cursor=cursor)
    patient_id = _check_patient(patient_id, start_date, end_date, cursor=cursor)

    # Create appointment
    event_id = _create_appointment(start_date, end_date, patient_id, doctor_id , nurses, cursor=cursor)
    return {
        "appointment_id": event_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id
    }

def _create_appointment(start_date, end_date, patient_id, doctor_id, nurses, cursor=None):
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

    if event is None:
        raise ValueError('Error creating event')
    
    return event

@transactional
def schedule_surgery(db_con, payload, hospitalization_id, login_id, cursor=None) -> Dict:
    start_date = get_dateobj_from_timestamp(payload['date'])
    end_date = start_date + datetime.timedelta(hours=1)
    patient_id = payload['patient_id'] 
    doctor_id = payload['doctor_id']    
    nurses:List[List] = payload['nurses']
    nurse_ids = [nurse[0] for nurse in nurses]

    if patient_id == login_id:
        raise ValueError('Cannot schedule surgery for yourself')
    if start_date < datetime.datetime.now():
        raise ValueError('Stop there time traveler!')
    
    # create hospitalization or validate it
    if hospitalization_id is None:
        hosp_duration = payload['hospitalization_duration']
        hosp_end_date = start_date + datetime.timedelta(days=hosp_duration)
        hosp_nurse_id = payload['hospitalization_nurse_id']

        #confirm entities are available
        _check_nurses([hosp_nurse_id], start_date, hosp_end_date, cursor=cursor)
        _check_patient(patient_id, start_date, hosp_end_date, cursor=cursor)

        hospitalization_id = _create_hospitalization(
            start_date, hosp_end_date, patient_id, hosp_nurse_id, cursor=cursor)
    else:
        _check_hospitalization(hospitalization_id, start_date, end_date, cursor=cursor)

    # confirm entities are available for surgery date
    nurse_ids = _check_nurses(nurse_ids, start_date, end_date, cursor=cursor)
    doctor_id = _check_doctor(doctor_id, start_date, end_date, cursor=cursor)
    patient_id = _check_patient(patient_id, start_date, end_date, cursor=cursor)

    surgery_id = _create_surgery(
        start_date, end_date, doctor_id, nurses, hospitalization_id, cursor=cursor)

    return {
        "hospitalization_id": hospitalization_id,
        "surgery_id": surgery_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id
    }

def _check_hospitalization(hospitalization_id, start_date, end_date, cursor=None):
    query = """
    SELECT h.event_id
    FROM hospitalization h
    JOIN event e ON h.event_id = e.id
    WHERE h.event_id = %s
    AND e.start_date < %s AND e.end_date > %s
    """
    values = (hospitalization_id, end_date, start_date)
    
    cursor.execute(query, values)
    hospitalization = cursor.fetchone()

    if hospitalization is None:
        raise ValueError('This hospitalization is unavailable')
    
    return hospitalization[0]

def _create_hospitalization(start_date, end_date, patient_id, nurse_id, cursor=None):
    cursor.execute(
        "INSERT INTO event (start_date, end_date, patient_person_id) VALUES (%s, %s, %s) RETURNING id",
        (start_date, end_date, patient_id)
    )

    event = cursor.fetchone()
    if event is None:
        raise ValueError('Error creating event')

    cursor.execute(
        "INSERT INTO hospitalization (event_id, nurse_employee_person_id) VALUES (%s, %s)",
        (event, nurse_id)
    )

    return event[0]

def _create_surgery(start_date, end_date, doctor_id, nurses, hospitalization_id, cursor=None):
    cursor.execute(
        "INSERT INTO surgery (start_date, end_date, hospitalization_event_id, doctor_employee_person_id) VALUES (%s, %s, %s, %s) RETURNING id",
        (start_date, end_date, hospitalization_id, doctor_id)
    )

    surgery = cursor.fetchone()
    if surgery is None:
        raise ValueError('Error creating event')

    data = [(surgery[0], nurse[0], nurse[1]) for nurse in nurses]
    # Insert the new nurse appointments
    cursor.executemany(
        "INSERT INTO nurse_surgery (surgery_id, nurse_employee_person_id, role) VALUES (%s, %s, %s)",
        data
    )

    return surgery[0]

@transactional
def get_prescriptions(db_con, patient_id, cursor=None) -> List[Dict]:
    query = """
    SELECT 
    p.id,
    TO_CHAR(p.validity, 'YYYY-MM-DD'),
    json_agg(
        json_build_object(
            'medication_id', m.id,
            'medication_name', m.name,
            'dosage', po.dosage,
            'frequency', po.frequency
        )
        ) AS posology_info
    FROM prescription p
    JOIN event e ON p.event_id = e.id
    JOIN patient pa ON e.patient_person_id = pa.person_id
    JOIN posology po ON po.prescription_id = p.id
    JOIN medication m ON m.id = po.medication_id
    WHERE pa.person_id = %s
    GROUP BY p.id
    """
    values = (patient_id,)
    cursor.execute(query, values)
    prescriptions = cursor.fetchall()
    
    if prescriptions is None:
        raise ValueError("Patient does not have any prescriptions")
    
    return [{
        "prescription_id": prescription[0],
        "validity": prescription[1],
        "posology": prescription[2]
    } for prescription in prescriptions]

@transactional
def add_prescription(db_con, payload, cursor=None) -> int:
    type = payload['type']
    event_id = payload['event_id']
    validity = get_dateobj_from_date(payload['validity'])

    cursor.execute(
        f"SELECT 1 FROM {type} WHERE event_id = %s",
        (event_id,)
    )
    if cursor.fetchone() is None:
        raise ValueError(f'Invalid {type} id')

    cursor.execute(
        "INSERT INTO prescription (event_id, validity) VALUES (%s, %s) RETURNING id",
        (event_id, validity)
    )
    prescription = cursor.fetchone()

    if prescription is None:
        raise ValueError('Error creating prescription')
    
    prescription_id = prescription[0]
    
    query = """ 
    INSERT INTO posology (prescription_id, medication_id, dosage, frequency)
    VALUES (%s, (SELECT id FROM medication WHERE name = %s), %s, %s)
    """
    values = [(prescription_id, med['medicine'], med['posology_dose'], med['posology_frequency']) 
                    for med in payload['medicines']]
    
    cursor.executemany(query, values)
    #could add a select count to validate medicines being added before committing, but seems pedantic
    
    return {
        "prescription_id": prescription_id,
        "event_id": event_id
    }

def _check_bill(login_id, bill_id, cursor=None):
    query = """
        SELECT b.status
        FROM bill b JOIN event e
        ON b.event_id = e.id
        WHERE b.id = %s
        AND e.patient_person_id = %s;
        """
    values = (bill_id, login_id)
    cursor.execute(query, values)

    bill = cursor.fetchone()

    if bill is None:
        raise ValueError('This bill is unavailable')
    if bill[0] == 'paid':
        raise ValueError('This bill has already been paid')
    
    return bill[0]

def _pay_amount(bill_id, payment_amount, payment_method, cursor=None):
    cursor.execute(
        "INSERT INTO payment (bill_id, amount, method) VALUES (%s, %s, %s) RETURNING id",
        (bill_id, payment_amount, payment_method)
    )

    payment = cursor.fetchone()
    if payment is None:
        raise ValueError('Error generating payment')

    query = """
        SELECT bill.amount - COALESCE((
            SELECT SUM(payment.amount)
            FROM payment
            WHERE payment.bill_id = bill.id), 0)as current_amount
        
        FROM bill
        WHERE bill.id = %s;
    """
    cursor.execute(query, (bill_id,))

    result = cursor.fetchone()
    if result is None:
        raise ValueError('Error paying bill')

    return result[0]

@transactional
def execute_payment(db_con, login_id, bill_id, payload, cursor=None):
    # needs to verify if bill's patient is the same as the login_id
    #TODO: meter aqui o valor do pagamento da payload
    payment_amount = float(payload['amount'])
    payment_method = payload['payment_method']

    bill_status = _check_bill(login_id, bill_id, cursor=cursor)
    current_amount = _pay_amount(bill_id, payment_amount, payment_method, cursor=cursor)

    if current_amount == 0:
        return f"Bill paid successfully."
    elif current_amount < 0:
        return f"Bill overpaid. Credited {-current_amount} euro."
    else:
        return f"Bill partially paid. Remaining amount: {current_amount} euro."

@transactional
def get_top3_patients(db_con, cursor=None):
    now = datetime.datetime.now()
    start_date = now.replace(day=1).date()
    end_date = datetime.date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    query = """
    WITH procedures AS (
        SELECT 
            'appointment' AS procedure_type,
            a.event_id AS procedure_id,
            a.doctor_employee_person_id AS doctor_id,
            TO_CHAR(e.start_date, 'YYYY-MM-DD HH24:MI') AS date,
            e.patient_person_id AS patient_id
        FROM appointment a
        JOIN event e ON a.event_id = e.id
        WHERE e.start_date >= %s AND e.end_date <= %s

        UNION ALL

        SELECT
            'surgery' AS procedure_type,
            s.id AS procedure_id,
            s.doctor_employee_person_id AS doctor_id,
            TO_CHAR(s.start_date, 'YYYY-MM-DD HH24:MI') AS date,
            esub.patient_person_id AS patient_id
        FROM surgery s 
        JOIN event esub ON s.hospitalization_event_id = esub.id
        WHERE s.start_date >= %s AND s.end_date <= %s
    )
    SELECT 
        p.name AS patient_name,
        COALESCE(SUM(payment.amount), 0) AS total_spent,
        json_agg(DISTINCT procedures.*) AS procedures
    FROM patient pt
    JOIN person p ON pt.person_id = p.id
    JOIN event e ON e.patient_person_id = pt.person_id
    JOIN bill b ON b.event_id = e.id
    JOIN payment ON payment.bill_id = b.id
    JOIN procedures ON procedures.patient_id = pt.person_id
    GROUP BY p.id
    ORDER BY total_spent DESC
    LIMIT 3;  
    """
    values = (start_date, end_date, start_date, end_date)
    cursor.execute(query, values)
    patients = cursor.fetchall()

    if patients is None:
        raise ValueError("No patients found")
    
    return [{
        "patient_name": patient[0],
        "total_spent": patient[1],
        "procedures": patient[2]
    } for patient in patients]

@transactional
def get_daily_summary(db_con, date, cursor=None):
    date = get_dateobj_from_date(date)
    date_plus_one = date + datetime.timedelta(days=1)
    query = """
    SELECT
        COUNT(DISTINCT e.id) AS hospitalizations,
        (SELECT COUNT(DISTINCT s.id) 
            FROM surgery s 
            WHERE s.start_date >= %s AND s.start_date < %s) AS surgeries,
        (SELECT COUNT(DISTINCT p.id)
            FROM prescription p
            JOIN event e ON p.event_id = e.id
            WHERE e.start_date >= %s AND e.start_date < %s) AS prescriptions,
        COALESCE(SUM(payment.amount), 0) AS total_revenue
    
    FROM hospitalization h 
    JOIN event e ON h.event_id = e.id 
    JOIN bill b ON b.event_id = e.id
    JOIN payment ON payment.bill_id = b.id
    WHERE e.start_date >= %s AND e.start_date < %s;
    """

    #considering this query's requirements and the prolonged nature of hospitalizations,
    # it might have made sense to add a created_at column to payment/prescription like:
    # ALTER TABLE prescriptions
    # ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;


    cursor.execute(query, (date, date_plus_one, date, date_plus_one,date, date_plus_one))
    summary = cursor.fetchone()

    if summary is None or summary[0] == 0:
        raise ValueError("No data found for this date")
    
    return {
        "hospitalizations": summary[0],
        "surgeries": summary[1],
        "prescriptions": summary[2],
        "amount spent": summary[3]
    }


@transactional
def generate_monthly_report(db_con, cursor=None):
    now = datetime.datetime.now()
    twelve_months_ago = now.replace(year= now.year - 1, day=1).date()
    end_of_this_month = datetime.date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    query = """
    WITH
    SurgeryCounts AS (
        SELECT
            s.doctor_employee_person_id,
            DATE_TRUNC('month', s.start_date) AS surgery_month,
            COUNT(*) AS surgery_count,
            ROW_NUMBER() OVER(PARTITION BY DATE_TRUNC('month', s.start_date) ORDER BY COUNT(*) DESC) as rn
        FROM surgery s
        WHERE s.start_date >= %s AND s.start_date <= %s
        GROUP BY
            s.doctor_employee_person_id,
            surgery_month
    )
    SELECT
        p.name AS doctor_name,
        TO_CHAR(sc.surgery_month, 'YYYY-MM') AS date,
        sc.surgery_count
    
    FROM SurgeryCounts sc
    JOIN doctor d ON sc.doctor_employee_person_id = d.employee_person_id
    JOIN employee e ON d.employee_person_id = e.person_id
    JOIN person p ON e.person_id = p.id
    WHERE sc.rn = 1
    
    ORDER BY sc.surgery_month;
    """

    cursor.execute(query, (twelve_months_ago, end_of_this_month))
    top12 = cursor.fetchall()

    if top12 is None:
        raise ValueError("No doctors or surgeries found")

    return [{
        "month": top[1],
        "doctor name": top[0],
        "surgeries": top[2]
        } for top in top12]
