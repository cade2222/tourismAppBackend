from flask import Blueprint

bp = Blueprint("event", __name__, url_prefix="/event")

# create event creation, management, joining, and chat hooks here