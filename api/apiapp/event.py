from flask import Blueprint
from .auth import authenticate

bp = Blueprint("event", __name__, url_prefix="/event")

# create event creation, management, joining, and chat hooks here