from flask import Blueprint, request, g, abort
import psycopg
import psycopg.types.composite
from .auth import authenticate

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

def create_event(displayname: str, description: str | None = None, location: dict | None = None, **kwargs) -> None:
    """
    Adds an event with the given information to the database.
    """
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO events(displayname, description, host) VALUES (%s, %s, %s) RETURNING id;", 
                    (displayname, description if description is not None else "", g.userid))
        if location is not None:
            id, = cur.fetchone()
            cur.execute("UPDATE events SET coords = '(%s,%s)' WHERE id = %s;", (float(location["lat"]), float(location["lon"]), id))

@bp.route("/create", methods=["POST"])
@authenticate
def create():
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
        - 400 if the JSON is malformatted.
        - 422 if the JSON is not of the right type or does not contain the right values.
        - 200 if the JSON is semantically correct, even if other errors are returned.
    
    If a 200 status code is returned, the response body will contain a JSON array of error objects containing the following properties:
        - `field`: the top-level field in which the error occurred
        - `description`: a description of the error
    
    If this array is non-empty, the request was not successful.
    If the array is empty, the request can be assumed to have been successful.
    """
    if request.json is None:
        abort(415)
    if not isinstance(request.json, dict):
        abort(422)
    if "displayname" not in request.json or not isinstance(request.json["displayname"], str):
        abort(422)
    if "description" in request.json and not isinstance(request.json["description"], str):
        abort(422)
    if "location" in request.json:
        if not isinstance(request.json["location"], dict):
            abort(422)
        if "lat" not in request.json["location"] or "lon" not in request.json["location"]:
            abort(422)
        try:
            _ = float(request.json["location"]["lat"])
            _ = float(request.json["location"]["lon"])
        except ValueError:
            abort(422)
    errors = validate_create_inputs(**request.json)
    if not errors:
        create_event(**request.json)
    return errors
