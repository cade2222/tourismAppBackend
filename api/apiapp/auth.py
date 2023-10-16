from flask import Blueprint, request, g, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Unauthorized
import psycopg
import re
import sys

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["POST"])
def create_account():
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
    if re.compile(r"^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[ -/:-@\[-`{-~])[ -~]{8,}$").match(password) is None:
        errors.append({"field": "password", "description": "Password must be at least 8 characters, contain only ASCII characters, and contain at least one uppercase letter, lowercase letter, number, and special character."})
    if re.compile(r"^(?!.{256,})[ -?A-~]+@[A-z]([A-z0-9\-]*[A-z0-9])?(\.[A-z]([A-z0-9\-]*[A-z0-9]))*$").match(email) is None:
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
def login():
    if request.authorization is None or request.authorization.type != "basic":
        abort(401)
    username = request.authorization.parameters.get("username")
    password = request.authorization.parameters.get("password")
    if username is None or password is None:
        abort(401)
    
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT password FROM users WHERE username = %s;", (username,))
        if cur.rowcount == 0:
            abort(401)
        passwordhash, = cur.fetchone()
        if not check_password_hash(passwordhash, password):
            abort(401)
    
    return "Success"

@bp.errorhandler(Unauthorized)
def send_www_authenticate(error) -> Response:
    return Response("Incorrect login supplied.", 401, {"WWW-Authenticate": "Basic realm=\"Login Required\""})