from flask import Blueprint
from dataclasses import dataclass

bp = Blueprint("location", __name__, url_prefix="/location")

@dataclass
class Point:
    lat: float
    lon: float

# create location-posting functions