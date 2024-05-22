import psycopg2
from src.utils import logger, UserDetails

def create_connection(db_name, db_host, db_port, db_user, db_pass):
    db = psycopg2.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        database=db_name
    )
    return db


def register_user(db_con, user_type, payload):
    cursor = db_con.cursor()
    # inserts into n keys, n values
    cursor.execute(
        f"INSERT INTO {user_type} ({', '.join(payload.keys())}) VALUES ({', '.join(['%s']*len(payload.keys()))})",
        tuple(payload.values())
    )
    db_con.commit()
    cursor.close()

def get_user(db_con, user_id):
    pass

def get_top3_patients(db_con):
    pass