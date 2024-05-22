import psycopg2

def db_connection(db_name, db_host, db_port, db_user, db_pass):
    db = psycopg2.connect(
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        database=db_name
    )
    return db