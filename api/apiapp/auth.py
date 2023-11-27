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
    inner.__name__ = func.__name__
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
    if re.compile(r"^(?!.{256,})[ -?A-~]+@[A-z0-9]([A-z0-9\-]*[A-z0-9])?(\.[A-z0-9]([A-z0-9\-]*[A-z0-9]))*$", re.IGNORECASE).match(email) is None:
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


def create_user(username: str, password: str, email: str, displayname: str | None = None, **kwargs) -> int:
    """
    Adds a user with the given name, password, and email address (and, optionally, display name) to the database.

    Returns an error list on failure (see docstring for `register()`).
    """
    passwordhash = generate_password_hash(password)

    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("INSERT INTO users(username, password, email) VALUES (%s, %s, %s) RETURNING id;", (username.lower(), passwordhash, email.lower()))
        id, = cur.fetchone()
        if displayname is not None and len(displayname) != 0:
            cur.execute("UPDATE users SET displayname = %s WHERE id = %s;", (displayname, id))
        return id


def send_verification_email(username: str, email: str, **kwargs) -> None:
    """
    Sends a verification email to the given email.
    """
    pass


@bp.route("", methods=["POST"])
def register() -> Response:
    """
    Registers a new user into the database.

    HTTP Method: POST

    Input: a JSON object with the following values:
        - `username`: the new user's username
        - `password`: the new user's password
        - `email`: the new user's email
        - `displayname` (optional): the new user's display name, or NULL / empty string for none
    
    Status Codes:
        - 415 if the request was not in JSON format.
        - 400 if the JSON was malformatted, did not contain the correct fields, or they were the wrong data type.
        - 422 if the JSON syntax was correct but the request could not be processed.
        - 200 if the request succeeded.

    If a 422 status code is returned, the response body will contain a JSON array of errors in the following format:
        - `field`: the field in which the error occurred
        - `description`: a description of the error
    
    If a 200 status code is returned, the response body will contain a JSON object containing the following properties:
        - `id`: the ID of the user
    
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
        abort(400)
    if "username" not in request.json or "password" not in request.json or "email" not in request.json:
        abort(400)
    if not isinstance(request.json["username"], str) or not isinstance(request.json["password"], str) \
        or not isinstance(request.json["email"], str) \
        or ("displayname" in request.json and not isinstance(request.json["displayname"], str)):
        abort(400)
    
    errors = validate_registration(**request.json)
    if not errors:
        errors = check_conflicts(**request.json)
    if errors:
        return (errors, 422)

    id = create_user(**request.json)
    send_verification_email(**request.json)
    return {"id": id}


def is_verified() -> bool:
    """
    Determines if the logged-in user has a verified email.

    Returns true if the account is verified, false otherwise.
    """
    assert isinstance(g.conn, psycopg.Connection)
    assert isinstance(g.userid, int)
    verified = False
    with g.conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s AND verification IS NULL;", (g.userid,))
        verified = cur.rowcount != 0
    return verified

@bp.route("", methods=["GET"])
@authenticate
def login() -> Response:
    """
    Returns a 200 status code if the given HTTP authorization is valid, or 401 if not.
    Response body is a JSON object with two fields:
        - `id`: the user's ID
        - `displayname`: the user's display name, or `null` if none is set
    """
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT displayname FROM users WHERE id = %s;", (g.userid,))
        dname, = cur.fetchone()
        return {"id": g.userid, "displayname": dname}


def verify_email(code: int, email: str, **kwargs) -> Response:
    """
    Verifies the given email with the given code.

    Returns True on success, False on failure.
    """
    success = False
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT verification FROM users WHERE email = %s;", (email.lower()))
        if cur.rowcount == 0:
            abort(422)
        actualcode, = cur.fetchone()
        if actualcode is None:
            return ("", 204)
        elif code != actualcode:
            abort(422)
        cur.execute("UPDATE users SET verification = NULL WHERE email = %s;", (email.lower(), code))
        return ("", 201)

@bp.route("/verify", methods=["PUT"])
def verify() -> Response:
    """
    Verifies the given email.

    Input: a JSON object in the following format:
        - `email`: the email to verify
        - `code`: the verification code
    
    Status Codes:
        - 415 if the request was not in JSON format.
        - 400 if the JSON was malformatted, did not contain the correct fields, or they were the wrong data type.
        - 422 if the JSON syntax was correct but the email was not verified.
        - 201 if the email was verified.
        - 204 if the email was already verified.
    
    If a 200 status code is returned, the response body will contain a JSON object containing the following properties:
        - `id`: the ID of the user
    """
    if request.json is None:
        abort(415)
    if not isinstance(request.json, dict):
        abort(400)
    if "email" not in request.json or not isinstance(request.json["email"], str):
        abort(400)
    if "code" not in request.json or not isinstance(request.json["code"], int):
        abort(400)
    return verify_email(**request.json)