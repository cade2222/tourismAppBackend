from flask import request, g
import psycopg2

def connect() -> None:
    """
    Connect to the database and add the handle to the app context's globals.
    """
    filename = request.environ.get("PSQL_CONF")
    if filename is None:
        raise RuntimeError("Environment variable PSQL_CONF is not set.")
    connstr = None
    try:
        file = open(filename)
        connstr = file.read()
    except OSError:
        raise RuntimeError("Could not open PSQL_CONF.")
    finally:
        file.close()
    
    try:
        g.conn = psycopg2.connect(connstr)
    except psycopg2.Error as e:
        raise RuntimeError(e.pgerror)

def disconnect() -> None:
    """
    Close the database connection stored in the app context.
    """
    g.conn.close()