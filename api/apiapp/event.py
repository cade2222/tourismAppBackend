from flask import Blueprint, request, g, abort
import psycopg
from .auth import authenticate

bp = Blueprint("event", __name__, url_prefix="/event")

def validate_create_inputs(displayname: str, description: str | None = None, **kwargs) -> list:
    if not displayname:
        return [{"field": "displayname", "description": "You must enter a display name."}]
    if len(displayname) > 255:
        return [{"field": "displayname", "description": "Display name must be less than 256 characters long."}]
    if description is not None and len(description) > 10000:
        return [{"field": "description", "description": "Description must be at most 10000 characters long."}]
    return []

def create_event(displayname: str, description: str | None = None, **kwargs) -> None:
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO events(displayname, description, host) VALUES (%s, %s, %s);", 
                    (displayname, description if description is not None else "", g.userid))

@bp.route("/create")
@authenticate
def create():
    if request.json is None:
        abort(415)
    if not isinstance(request.json, dict):
        abort(422)
    if "displayname" not in request.json or not isinstance(request.json["displayname"], str):
        abort(422)
    if "description" in request.json and not isinstance(request.json["description"], str):
        abort(422)
    errors = validate_create_inputs(**request.json)
    if not errors:
        create_event(**request.json)
    return errors
