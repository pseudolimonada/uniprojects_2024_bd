
import logging
import sys 

from dotenv import dotenv_values

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

# each key points to a value that is a list[str|list[str]] (lista de strings ou listas (elas proprias de strings))
UserDetails = {
    'patient': ['username','password','name','address','cc_number','nif_number','birthdate'],
    'assistant': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date']],
    'doctor': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date'],'license','specialization'],
    'nurse': ['username','password','name','address','cc_number','nif_number','birthdate',['contract_details','start_date','end_date']],
}

def setup_logger() -> logging.Logger:
    # Create logger
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create file handler and set level to debug
    fh = logging.FileHandler('log_file.log', 'a')
    fh.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')

    # Add formatter to ch and fh
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add ch and fh to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

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
            'APP_PORT': config['APP_PORT']
        }
        return parsed_config
    except KeyError as e:
        logger.error(f"Missing config key: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error converting config value to number: {str(e)}")
        sys.exit(1)

config = load_config()