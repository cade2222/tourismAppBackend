from flask import Blueprint, request, g, abort, Response
import psycopg
import psycopg.types.composite
from .auth import authenticate
from .location import Point

bp = Blueprint("event", __name__, url_prefix="/event")

def validate_create_inputs(displayname: str, description: str | None = None, location: dict | None = None, **kwargs) -> list:
    """
    Ensures the given event information is valid.

    Returns a list of errors (see docstring for `create()`), or an empty list if no issues were found.
    """
    errors = []
    if not displayname:
        errors.append({"field": "displayname", "description": "You must enter a display name."})
    if len(displayname) > 255:
        errors.append({"field": "displayname", "description": "Display name must be less than 256 characters long."})
    if description is not None and len(description) > 10000:
        errors.append({"field": "description", "description": "Description must be at most 10000 characters long."})
    if not -90.0 <= float(location["lat"]) <= 90.0:
        errors.append({"field": "location", "description": "Latitude must be between -90 and 90 degrees."})
    return errors

def create_event(displayname: str, description: str | None = None, location: dict | None = None, **kwargs) -> int:
    """
    Adds an event with the given information to the database.
    """
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO events(displayname, description, host) VALUES (%s, %s, %s) RETURNING id;", 
                    (displayname, description if description is not None else "", g.userid))
        id, = cur.fetchone()
        if location is not None:
            coords = Point(float(location["lat"]), float(location["lon"]))
            cur.execute("UPDATE events SET coords = %s WHERE id = %s;", (coords, id))
        return id

@bp.route("", methods=["POST"])
@authenticate
def create() -> Response:
    """
    API endpoint for creating a new event.

    Requires a JSON object in the request body with the following properties:
        - `displayname`: the name of the event
        - `description` (optional): a description of the event
        - `location` (optional): a JSON object containing the coordinates of the event
            - `lat`: the latitude, in degrees
            - `lon`: the longitude, in degrees
    
    The input data must meet the following requirements:
        - `displayname` must not be empty.
        - `displayname` must contain no more than 255 characters.
        - `description` must contain no more than 10000 characters.
        - `location.lat` must be between -90 and 90, inclusive
    
    The following status codes will be returned:
        - 415 if the request is not in JSON format.
        - 400 if the JSON is malformatted or does not contain the correct values.
        - 422 if the input data is invalid.
        - 200 if the creation was successful.
    
    If a 422 status code is returned, the response body will contain a JSON array of errors in the following format:
        - `field`: the field in which the error occurred
        - `description`: a description of the error
    
    If a 200 status code is returned, the response body will contain a JSON object containing the following properties:
        - `id`: the ID of the event
    """
    if request.json is None:
        abort(415)
    if not isinstance(request.json, dict):
        abort(400)
    if "displayname" not in request.json or not isinstance(request.json["displayname"], str):
        abort(400)
    if "description" in request.json and not isinstance(request.json["description"], str):
        abort(400)
    if "location" in request.json:
        if not isinstance(request.json["location"], dict):
            abort(400)
        if "lat" not in request.json["location"] or "lon" not in request.json["location"]:
            abort(400)
        try:
            _ = float(request.json["location"]["lat"])
            _ = float(request.json["location"]["lon"])
        except ValueError:
            abort(400)
    errors = validate_create_inputs(**request.json)
    if errors:
        return (errors, 422)
    return {"id": create_event(**request.json)}


def get_event_info(id: int) -> dict:
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    info = None
    with g.conn.cursor() as cur:
        cur.execute("SELECT displayname, description, coords FROM events WHERE id = %s;", (id,))
        if cur.rowcount == 0:
            return None
        name, description, location = cur.fetchone()
        info = {"displayname": name, "description": description, "location": None, "attendees": [], "attending": False}
        if location is not None:
            assert isinstance(location, Point)
            info["location"] = {"lat": location.lat, "lon": location.lon}
        cur.execute("SELECT attendees.userid, users.username, users.displayname FROM (attendees JOIN users ON users.id = attendees.userid) WHERE eventid = %s;", (id,))
        for row in cur:
            uid, uname, udname = row
            info["attendees"].append({"id": uid, "username": uname, "displayname": udname})
            if uid == g.userid:
                info["attending"] = True
    return info

@bp.route("/<int:eventid>", methods=["GET"])
@authenticate
def event_get(eventid: int) -> Response:
    info = get_event_info(eventid)
    if info is None:
        abort(404)
    return info


def event_add_user(eventid: int, userid: int) -> Response:
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)

    if userid != g.userid:
        abort(403)

    with g.conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM events WHERE id = %s;", (eventid,))
        count, = cur.fetchone()
        if count == 0:
            abort(404)
        cur.execute("SELECT COUNT(*) FROM attendees WHERE userid = %s AND eventid = %s;", (g.userid, eventid))
        count, = cur.fetchone()
        if count == 0:
            cur.execute("INSERT INTO attendees(userid, eventid) VALUES (%s, %s);", (g.userid, eventid))
            return ("", 201)
        else:
            return ("", 204)

@bp.route("/<int:eventid>/<int:userid>", methods=["PUT"])
@authenticate
def event_put(eventid: int, userid: int) -> Response:
    return event_add_user(eventid, userid)


def event_remove_user(eventid: int, userid: int) -> Response:
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    with g.conn.cursor() as cur:
        if g.userid != userid:
            cur.execute("SELECT host FROM events WHERE id = %s;", (eventid,))
            if cur.rowcount == 0:
                abort(404)
            host, = cur.fetchone()
            if g.userid != host:
                abort(403)
        cur.execute("DELETE FROM attendees WHERE userid = %s AND eventid = %s;", (userid, eventid))
        if cur.rowcount == 0:
            abort(404)
    return ("", 204)
        

@bp.route("/<int:eventid>/<int:userid>", methods=["DELETE"])
@authenticate
def event_user_delete(eventid: int, userid: int) -> Response:
    return event_remove_user(eventid, userid)