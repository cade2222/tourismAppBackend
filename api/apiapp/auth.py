from flask import Blueprint, request, g, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Unauthorized
import psycopg
import re

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


def validate_registration(username: str, password: str, email: str, displayname: str | None = None, **kwargs) -> list:
    """
    Ensures the validation requirements for the registration info are met (see docstring for `register()`).
    
    Returns an error list if not (see docstring for `register()`).
    """
    errors = []
    if re.compile(r"^([a-z0-9\-]){1,31}$", re.IGNORECASE).match(username) is None:
        errors.append({"field": "username", "description": "Username must be at most 31 characters and contain only alphanumeric characters and dashes."})
    if re.compile(r"^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[^0-9A-z])[ -~]{8,}$").match(password) is None:
        errors.append({"field": "password", "description": "Password must be at least 8 characters, contain only ASCII characters, and contain at least one uppercase letter, lowercase letter, number, and special character."})
    if re.compile(r"^(?!.{256,})[ -?A-~]+@[A-z0-9]([A-z0-9\-]*[A-z0-9])?(\.[A-z0-9]([A-z0-9\-]*[A-z0-9]))*$").match(email) is None:
        errors.append({"field": "email", "description": "Email is either too long or not valid."})
    if displayname is not None and len(displayname) > 63:
        errors.append({"field": "displayname", "description": "Display name cannot be more than 63 characters."})
    
    return errors

def check_conflicts(username: str, email: str, **kwargs) -> list:
    """
    Makes sure no other user with the given username and email exist in the database.

    Returns an error list on failure (see docstring for `register()`).
    """
    errors = []

    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s;", (username.lower(),))
        if cur.rowcount != 0:
            errors.append({"field": "username", "description": "Username is already taken."})
        cur.execute("SELECT id FROM users WHERE email = %s;", (email.lower(),))
        if cur.rowcount != 0:
            errors.append({"field": "email", "description": "Email is already taken."})
    
    return errors


def create_user(username: str, password: str, email: str, displayname: str | None = None, **kwargs) -> None:
    """
    Adds a user with the given name, password, and email address (and, optionally, display name) to the database.

    Returns an error list on failure (see docstring for `register()`).
    """
    errors = []

    passwordhash = generate_password_hash(password)

    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO users(username, password, email) VALUES (%s, %s, %s);", (username.lower(), passwordhash, email.lower()))
        if displayname is not None and len(displayname) != 0:
            cur.execute("UPDATE users SET displayname = %s WHERE username = %s;", (kwargs["displayname"], username))
    g.conn.commit()


def send_verification_email(username: str, email: str, **kwargs) -> None:
    """
    Sends a verification email to the given email.
    """
    pass


@bp.route("/register", methods=["POST"])
def register() -> Response:
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
        - `username` must contain only alphanumeric characters and hyphens ('-').
        - `password` must contain at least 8 characters, all ASCII.
        - `password` must contain at least one uppercase letter, one lowercase letter, one digit, and one special character.
        - `email` can be no more than 255 characters and must be in valid email address form.
        - `displayname` must contain no more than 63 characters.
    """
    if request.json is None:
        abort(415)
    if not isinstance(request.json, dict):
        abort(422)
    displayname = request.json.get("displayname")
    if "username" not in request.json or "password" not in request.json or "email" not in request.json:
        abort(422)
    if not isinstance(request.json["username"], str) or not isinstance(request.json["password"], str) \
        or not isinstance(request.json["email"], str) \
        or ("displayname" in request.json and not isinstance(request.json["displayname"], str)):
        abort(422)
    
    errors = validate_registration(**request.json)
    if len(errors) == 0:
        errors = check_conflicts(**request.json)
    if len(errors) == 0:
        create_user(**request.json)
        send_verification_email(**request.json)
    return errors


@bp.route("/login", methods=["GET"])
@authenticate
def login() -> Response:
    """
    Returns a 200 status code if the given HTTP authorization is valid, or 401 if not.
    """
    return "Success"


def verify_email(code: int, email: str, **kwargs) -> bool:
    """
    Verifies the given email with the given code.

    Returns True on success, False on failure.
    """
    retval = False
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("UPDATE users SET verification = NULL WHERE email = %s AND verification = %s;", (email.lower(), code))
        retval = cur.rowcount != 0
    g.conn.commit()
    return retval

@bp.route("/verify/<int:code>", methods=["PUT"])
def verify(**kwargs) -> Response:
    """
    Verifies the given email.

    Input: a JSON object in the following format:
        - `email`: the email to verify

    Output: a JSON array in the following format:
        - `success`: true if verification was successful, false otherwise
    
    Status Codes:
        - 415 if the type was not JSON
        - 422 if the input did not contain the required fields
        - 200 otherwise (even if the verification failed; see JSON output for actual result)
    """
    if request.json is None or not isinstance(request.json, dict):
        abort(415)
    if "email" not in request.json or not isinstance(request.json["email"], str):
        abort(422)
    return {"success": verify_email(**kwargs, **request.json)}