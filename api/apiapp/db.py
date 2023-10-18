from flask import request, g, Blueprint, Response
import psycopg
import psycopg.adapt
import re
from .location import Point
import sys

class PointDumper(psycopg.adapt.Dumper):
    oid = psycopg.adapters.types["point"].oid
    def dump(self, obj: Point) -> bytes:
        return ("(%s, %s)" % (obj.lat, obj.lon)).encode()

class PointLoader(psycopg.adapt.Loader):
    def load(self, data: memoryview) -> Point:
        print(data.tobytes().decode(), file=sys.stderr)
        m = re.match(r"\(([^)]+),([^)]+)\)", data.tobytes().decode())
        try:
            if m is not None:
                return Point(float(m.group(1)), float(m.group(2)))
            else:
                raise ValueError()
        except:
            raise psycopg.InterfaceError("Incorrect Point representation")

bp = Blueprint("db", __name__)

@bp.before_app_request
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
        g.conn = psycopg.connect(connstr, autocommit=True)
        g.conn.adapters.register_dumper(Point, PointDumper)
        g.conn.adapters.register_loader("point", PointLoader)
    except psycopg.Error as e:
        raise RuntimeError(e.pgerror)

@bp.after_app_request
def disconnect(response: Response) -> Response:
    """
    Close the database connection stored in the app context.
    """
    g.conn.close()
    return response