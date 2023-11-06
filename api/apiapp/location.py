from flask import Blueprint, g, request, Response, abort
from dataclasses import dataclass
from geopy.distance import geodesic as gd
import psycopg
import googlemaps
import googlemaps.geocoding
import googlemaps.places

bp = Blueprint("location", __name__, url_prefix="/location")

@dataclass
class Place:
    id: str
    name: str
    types: list[str]

@dataclass
class Point:
    lat: float
    lon: float

    def distanceto(self, dest) -> gd:
        assert isinstance(dest, Point)
        return gd((self.lat, self.lon), (dest.lat, dest.lon))
    
    def getplaces(self) -> list[Place]:
        response = googlemaps.geocoding.reverse_geocode(client=g.gmaps, latlng=(self.lat, self.lon), result_type="point_of_interest")
        assert isinstance(g.conn, psycopg.Connection)
        places = []
        with g.conn.cursor() as cur:
            for i in response:
                id = i["place_id"]
                cur.execute("SELECT COUNT(*) FROM places WHERE id = %s;", (id,))
                count, = cur.fetchone()
                if count == 0:
                    name = googlemaps.places.place(client=g.gmaps, place_id=id, fields=["name"])["result"]["name"]
                    cur.execute("INSERT INTO places(id, name) VALUES (%s, %s);", (id, name))
                    for t in i["types"]:
                        cur.execute("INSERT INTO placetypes(id, type) VALUES (%s, %s);", (id, t))
                cur.execute("SELECT name FROM places WHERE id = %s;", (id,))
                name, = cur.fetchone()
                cur.execute("SELECT type FROM placetypes WHERE id = %s;", (id,))
                types = [i[0] for i in cur.fetchall()]
                places.append(Place(id, name, types))
        return places


@bp.before_app_request
def get_google_api_key():
    with open(request.environ["GOOGLE_API_KEY_PATH"]) as file:
        google_api_key = file.read()
        g.gmaps = googlemaps.Client(key=google_api_key)

def visit_location(location: Point, eventid: int) -> Response:
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM events WHERE id = %s;", (eventid,))
        count, = cur.fetchone()
        if count == 0:
            abort(404)
        places = location.getplaces()
        for i in places:
            cur.execute("SELECT COUNT(*) FROM locations WHERE placeid = %s AND eventid = %s;", (i.id, eventid))
            count, = cur.fetchone()
            if count == 0:
                cur.execute("INSERT INTO locations(placeid, eventid) VALUES (%s, %s);", (i.id, eventid))
            cur.execute("UPDATE locations SET visits = visits + 1 WHERE placeid = %s AND eventid = %s;", (i.id, eventid))
    return ("", 204)


@bp.route("/event/<int:eventid>", methods=["POST"])
def location_get(eventid: int):
    if request.json is None:
        abort(415)
    if "lat" not in request.json or "lon" not in request.json:
        abort(400)
    try:
        lat = float(request.json["lat"])
        lon = float(request.json["lon"])
        location = Point(lat, lon)
        return visit_location(location, eventid)
    except ValueError:
        abort(400)
    