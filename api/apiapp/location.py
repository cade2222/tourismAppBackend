from flask import Blueprint
from dataclasses import dataclass
from geopy.distance import geodesic as gd

bp = Blueprint("location", __name__, url_prefix="/location")

@dataclass
class Point:
    lat: float
    lon: float

    def distanceto(self, dest):
        assert isinstance(dest, Point)
        return gd((self.lat, self.lon), (dest.lat, dest.lon))

# create location-posting functions