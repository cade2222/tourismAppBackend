from flask import Blueprint, request, g, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Unauthorized
import psycopg
import re
import sys

bp = Blueprint("auth", __name__, url_prefix="/auth")


def authenticate(func):
    """
    Requires HTTP Basic Authentication before a request is processed.
    On failure, returns a 401 status code.
    On success, sets `g.userid` to the authenticated user's ID.
    """
    def inner(*args, **kwargs):
        if request.authorization is None or request.authorization.type != "basic":
            abort(401)
        username = request.authorization.parameters["username"]
        password = request.authorization.parameters["password"]
        
        assert isinstance(g.conn, psycopg.Connection)
        with g.conn.cursor() as cur:
            cur.execute("SELECT password, id FROM users WHERE username = %s;", (username,))
            if cur.rowcount == 0:
                abort(401)
            passwordhash, id = cur.fetchone()
            if not check_password_hash(passwordhash, password):
                abort(401)
            g.userid = id
        
        return func(*args, **kwargs)
    return inner


@bp.app_errorhandler(Unauthorized)
def send_www_authenticate(error) -> Response:
    """
    Send a WWW-Authenticate header when a request is unauthorized.
    """
    return Response("Incorrect login supplied.", 401, {"WWW-Authenticate": "Basic realm=\"Login Required\""})



@bp.route("/register", methods=["POST"])
def create_account():
    """
    Registers a new user into the database.

    HTTP Method: POST

    Input: a JSON object with the following values:
        - `username`: the new user's username
        - `password`: the new user's password
        - `email`: the new user's email
        - `displayname` (optional): the new user's display name, or NULL / empty string for none

        
    Output: a JSON array with objects of the following format:
        - `field`: the JSON field that contained an error
        - `description`: why the field was in error

    If the request was successful, an empty array will be returned.
    
    Status Codes:
        - 415 if the request was not in JSON format.
        - 422 if the JSON format did not contain the correct fields, or they were the wrong data type.
        - 200 if the syntax was correct, even if the request was not processed correctly.
    
    The following requirements are in place for the inputs:
        - `username` must contain no more than 31 characters.
        - `username` must contain only alphanumeric characters and hyphens ('-')
        - `password` must contain at least 8 characters, all ASCII
        - `password` must contain at least one uppercase letter, one lowercase letter, one digit, and one special character
        - `email` can be no more than 255 characters and must be in valid email address form
    """
    if request.json is None:
        abort(415)
    username = request.json.get("username")
    password = request.json.get("password")
    email = request.json.get("email")
    displayname = request.json.get("displayname")
    if username is None or password is None or email is None:
        abort(422)
    if not isinstance(username, str) or not isinstance(password, str) or not isinstance(email, str) or (displayname is not None and not isinstance(displayname, str)):
        abort(422)
    errors = []
    if re.compile(r"^([a-z0-9\-]){1,31}$", re.IGNORECASE).match(username) is None:
        errors.append({"field": "username", "description": "Username must be at most 31 characters and contain only alphanumeric characters and dashes."})
    if re.compile(r"^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[^0-9A-z])[ -~]{8,}$").match(password) is None:
        errors.append({"field": "password", "description": "Password must be at least 8 characters, contain only ASCII characters, and contain at least one uppercase letter, lowercase letter, number, and special character."})
    if re.compile(r"^(?!.{256,})[ -?A-~]+@[A-z0-9]([A-z0-9\-]*[A-z0-9])?(\.[A-z0-9]([A-z0-9\-]*[A-z0-9]))*$").match(email) is None:
        errors.append({"field": "email", "description": "Email is either too long or not valid."})
    
    if len(errors) != 0:
        return errors
    
    passwordhash = generate_password_hash(password)

    assert isinstance(g.conn, psycopg.Connection)

    with g.conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s;", (username.lower(),))
        if cur.rowcount != 0:
            errors.append({"field": "username", "description": "Username is already taken."})
        cur.execute("SELECT id FROM users WHERE email = %s;", (email.lower(),))
        if cur.rowcount != 0:
            errors.append({"field": "email", "description": "Email is already taken."})
    if len(errors) != 0:
        return errors
    
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO users(username, password, email) VALUES (%s, %s, %s);", (username, passwordhash, email))
        if (displayname is not None and len(displayname) != 0):
            cur.execute("UPDATE users WHERE username = %s SET displayname = %s;", (username, displayname))
    g.conn.commit()

    return []


@bp.route("/login", methods=["GET"])
@authenticate
def login():
    """
    Returns a 200 status code if the given HTTP authorization is valid, or 401 if not.
    """
    return "Success"