import logging
import datetime
import sys 
from dotenv import dotenv_values


STATUS_CODES = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

USER_DETAILS = ['username','password','name','address','cc_number','nif_number','birth_date']

USER_TYPE_DETAILS = {
    'patient': ['medical_history'],
    'assistant': ['contract_details', 'certification_details'],
    'doctor': ['contract_details','license','specialization_name'],
    'nurse': ['contract_details'],
}

APPOINTMENT_DETAILS = ['doctor_id','date','nurses'] #nurses is a list of lists with id and role

SURGERY_DETAILS = ['doctor_id','date','nurses','hospitalization_duration', 'hospitalization_nurse_id'] #head nurse

PRESCRIPTION_DETAILS = ['type','event_id','validity','medicines']

PRESCRIPTION_MED_DETAILS = ['medicine','posology_dose','posology_frequency']

PAYMENT_DETAILS = ['amount','payment_method']

def setup_logger() -> logging.Logger:
    # Create logger
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)

    # Create console handler and file handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log_file.log', 'a')
    fh.setLevel(logging.DEBUG)

    # Format handlers
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

logger = setup_logger()



def load_config() -> dict:
    try:
        config = dotenv_values(".env")
        parsed_config = {
            'DB_USER': config['DB_USER'],
            'DB_PASS': config['DB_PASS'],
            'DB_HOST': config['DB_HOST'],
            'DB_PORT': config['DB_PORT'],
            'DB_NAME': config['DB_NAME'],
            'APP_HOST': config['APP_HOST'],
            'APP_PORT': config['APP_PORT'],
            'APP_SECRET_KEY': config['APP_SECRET_KEY']
        }
        return parsed_config
    except KeyError as e:
        logger.error(f"Missing config key: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error converting config value to number: {str(e)}")
        sys.exit(1)

config = load_config()

def get_date_from_dateobj(date: datetime.date):
    try:
        return date.strftime('%Y-%m-%d')
    except AttributeError as e:
        raise ValueError(f"Invalid date object: {str(e)}")

def get_timestamp_from_dateobj(timestamp: datetime.datetime):
    try:
        return timestamp.strftime('%Y-%m-%d %Hh')
    except AttributeError as e:
        raise ValueError(f"Invalid timestamp object: {str(e)}")

def get_dateobj_from_date(date_str: str):
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError as e:
        raise ValueError(f"Invalid date string: {str(e)}")

def get_dateobj_from_timestamp(timestamp_str: str):
    try:
        return datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H')
    except ValueError as e:
        raise ValueError(f"Invalid timestamp string: {str(e)}")
