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
    name: str | None
    addr : str
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
                addr = i["formatted_address"]
                coords = i["geometry"]["location"]
                lat = float(coords["lat"])
                lon = float(coords["lng"])
                loc = Point(lat, lon)
                cur.execute("SELECT COUNT(*) FROM places WHERE id = %s;", (id,))
                count, = cur.fetchone()
                if count == 0:
                    name = googlemaps.places.place(client=g.gmaps, place_id=id, fields=["name"])["result"]["name"]
                    cur.execute("INSERT INTO places(id, name, address, coords) VALUES (%s, %s, %s);", (id, name, addr, loc))
                    for t in i["types"]:
                        cur.execute("INSERT INTO placetypes(id, type) VALUES (%s, %s);", (id, t))
                cur.execute("SELECT name FROM places WHERE id = %s;", (id,))
                name, = cur.fetchone()
                cur.execute("SELECT type FROM placetypes WHERE id = %s;", (id,))
                types = [i[0] for i in cur.fetchall()]
                places.append(Place(id, name, types))
        return places

def get_place_info(placeid: str) -> tuple[str | None, str, Point] | None:
    assert isinstance(g.conn, psycopg.Connection)
    with g.conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM places WHERE id = %s;", (placeid, ))
        count, = cur.fetchone()
        if count != 0:
            cur.execute("SELECT name, address, coords FROM places WHERE id = %s;", (placeid,))
            name, addr, loc = cur.fetchone()
            return name, addr, loc
        response = googlemaps.geocoding.geocode(client=g.gmaps, place_id=placeid)
        if response:
            addr = response[0]["formatted_address"]
            coords = response[0]["geometry"]["location"]
            lat = float(coords["lat"])
            lon = float(coords["lng"])
            loc = Point(lat, lon)
            cur.execute("INSERT INTO places(id, address, coords) VALUES (%s, %s, %s);", (placeid, addr, loc))
            name = None
            if "point_of_interest" in response[0]["types"]:
                name = googlemaps.places.place(client=g.gmaps, place_id=placeid, fields=["name"])["result"]["name"]
                cur.execute("UPDATE places SET name = %s WHERE id = %s;", (name, placeid))
                for t in response[0]["types"]:
                    cur.execute("INSERT INTO placetypes(id, type) VALUES (%s, %s);", (placeid, t))
            return (name, addr, loc)
        return None



@bp.before_app_request
def get_google_api_key():
    with open(request.environ["GOOGLE_API_KEY_PATH"]) as file:
        g.google_api_key = file.read()
        g.gmaps = googlemaps.Client(key=g.google_api_key)

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
    