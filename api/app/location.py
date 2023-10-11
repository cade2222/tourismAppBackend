from flask import Blueprint

bp = Blueprint("location", __name__, url_prefix="/location")

# create location-posting functions