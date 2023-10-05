from flask import Flask, request
from contextlib import contextmanager
import psycopg2
import psycopg2.extras

@contextmanager
def dbcursor():
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
        conn = psycopg2.connect(connstr)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        yield cur
    except psycopg2.Error as e:
        raise RuntimeError(e.pgerror)
    finally:
        cur.close()
        conn.close()


app = application = Flask(__name__)


@app.route('/')
def hello():
    return '<h1>Hello, World!</h1>'


@app.route('/apicall')
def apicall():
    users = []
    with dbcursor() as cur:
        cur.execute("SELECT username, displayname, email FROM Users;")
        for row in cur:
            users.append(dict(row))
    return users