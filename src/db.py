import psycopg2

def create_connection(db_name, db_host, db_port, db_user, db_pass):
    db = psycopg2.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        database=db_name
    )
    return db


def register_user(db_con, payload):
    pass