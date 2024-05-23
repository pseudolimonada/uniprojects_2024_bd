import flask
import jwt
from functools import wraps
from jwt import ExpiredSignatureError, InvalidTokenError

import src.db as db
from src.db import db_pool
from src.utils import config


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
        if 'x-access-tokens' in flask.request.headers:
            token = flask.request.headers['x-access-tokens']

        if not token:
            return flask.jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = db.check_user(flask.g.db_con, data['user_id'])
            user_type = data['user_type']

        except jwt.ExpiredSignatureError:
            return flask.jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return flask.jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return flask.jsonify({'message': str(e)}), 500

        return f(user_id, user_type, *args, **kwargs)

    return decorated