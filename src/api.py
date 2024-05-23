import flask
import jwt
from functools import wraps
from psycopg2 import DatabaseError

import src.db as db
from src.db import db_pool
from src.utils import config, logger, STATUS_CODES


app = flask.Flask(__name__)
app.config['SECRET_KEY'] = config['APP_SECRET_KEY']


@app.before_request
def before_request():
    if 'db_con' not in flask.g:
        flask.g.db_con = db_pool.getconn()

@app.teardown_appcontext
def close_db(e=None):
    db_con = flask.g.pop('db_con', None)
    if db_con is not None:
        db_pool.putconn(db_con)


# authorization decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'auth-token' in flask.request.headers:
            token = flask.request.headers['auth-token']

        if not token:
            return flask.jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            kwargs['login_id'] = db.check_user(flask.g.db_con, data['login_id'])
            kwargs['login_types'] = data['login_types']

        except jwt.ExpiredSignatureError:
            return flask.jsonify({'status': STATUS_CODES['api_error'], 'errors': f"Expired token error: {str(e)}"})
        except jwt.InvalidTokenError:
            return flask.jsonify({'status': STATUS_CODES['api_error'], 'errors': f"Invalid token error: {str(e)}"})
        except Exception as e:
            return flask.jsonify({'status': STATUS_CODES['internal_error'], 'errors': str(e)})

        return f(*args, **kwargs)

    return decorated


def endpoint_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Error: {e}")
            response = {'status': STATUS_CODES['api_error'], 'errors': str(e)}
            return response
        except (Exception, DatabaseError) as e:
            logger.exception(f"Error: {e}")
            response = {'status': STATUS_CODES['internal_error'],'errors': str(e)}
            return response
    return wrapper
