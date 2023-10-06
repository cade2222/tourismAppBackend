from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

# create registration, login, email verification, and user settings hooks here