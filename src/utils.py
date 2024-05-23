
import logging
import sys 

from dotenv import dotenv_values


STATUS_CODES = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

USER_DETAILS = ['username','password','name','address','cc_number','nif_number','birthdate']

OTHER_USER_DETAILS = {
    'patient': ['medical_record'],
    'assistant': ['contract'],
    'doctor': ['contract','license','specialization'],
    'nurse': ['contract'],
}

CONTRACT_DETAILS = ['contract_details', 'start_date', 'end_date']


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