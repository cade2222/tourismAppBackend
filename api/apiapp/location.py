from flask import Blueprint
from dataclasses import dataclass
import re

bp = Blueprint("location", __name__, url_prefix="/location")

@dataclass
class Point:
    lat: float
    lon: float

    def __init__(self, sqlrep: str):
        m = re.match(r"\(([^)]+),([^)])\)", sqlrep.decode())
        try:
            if m is not None:
                self.lat = float(m.group(1))
                self.lon = float(m.group(2))
            else:
                raise ValueError()
        except:
            raise ValueError("Incorrect representation")


# create location-posting functions