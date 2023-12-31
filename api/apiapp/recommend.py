from flask import Blueprint, g, request, abort
from .auth import authenticate
from .location import Point
import googlemaps.places
import psycopg
from dataclasses import dataclass

bp = Blueprint("recommend", __name__, url_prefix="/recommend")

@bp.route("", methods=["GET"])
@authenticate
def get_recommendations():
    """
    Gets a list of recommendations based on a user's location and search query.

    Inputs (given as URL params):
        - `q`: the category of recommendations to search (e.g., "restaurants")
        - `lat`, `lon`: the user's coordinates, in degrees
        - `rad` (optional): the search radius, in miles (defaults to 10, only a preference)
    
    Outputs a JSON array of recommendations in the following format:
        - `name`: the name of the recommendation
        - `location`: the coordinates of the recommendation, as an object:
            - `lat`, `lon`: the latitude and longitude, in degrees
        - `address`: the address of the recommendation
        - `distance`: the distance from the user to the recommended place, in miles
    """
    assert isinstance(g.conn, psycopg.Connection)
    if "q" not in request.args or not request.args["q"].strip():
        abort(400)
    category = request.args["q"].strip()
    if "lat" not in request.args or "lon" not in request.args:
        abort(400)
    loc = None
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            abort(400)
        loc = Point(lat, lon)
    except ValueError:
        abort(400)
    radius = 16093.44
    if "rad" in request.args:
        try:
            radius = float(request.args["rad"]) * 1609.344
        except ValueError:
            pass
    
    res = googlemaps.places.places(g.gmaps, query=category, location=(loc.lat, loc.lon), radius=radius)

    @dataclass
    class Recommendation:
        index: int
        place: dict
        visits: int
    places = []
    for c in res["results"]:
        places.append(Recommendation(len(places), c, 0))
    with g.conn.cursor() as cur:
        for c in places:
            cur.execute("SELECT COUNT(*) FROM places WHERE id = %s;", (c.place["place_id"],))
            count, = cur.fetchone()
            if (count == 0):
                cur.execute("INSERT INTO places(id, name, address, coords) VALUES (%s, %s, %s, %s);",
                            (c.place["place_id"], c.place["name"], c.place["formatted_address"],
                             Point(c.place["geometry"]["location"]["lat"], c.place["geometry"]["location"]["lng"])))
                for t in c.place["types"]:
                    cur.execute("INSERT INTO placetypes(id, type) VALUES (%s, %s);", (c.place["place_id"], t))
        cur.execute("SELECT eventid FROM attendees WHERE userid = %s;", (g.userid,))
        events = []
        for row in cur:
            eid, = row
            events.append(eid)
        cur.execute("SELECT placeid, SUM(visits) FROM locations WHERE eventid = ANY(%s) GROUP BY placeid;", (events,))
        for row in cur:
            pid, visits = row
            for p in places:
                if p.place["place_id"] == pid:
                    p.visits = visits
                    break
        places.sort(key=lambda x: x.visits + x.index)
        ret = []
        for p in places:
            ret.append({
                "name": p.place["name"],
                "address": p.place["formatted_address"],
                "location": {
                    "lat": p.place["geometry"]["location"]["lat"],
                    "lon": p.place["geometry"]["location"]["lng"]
                },
                "distance": loc.distanceto(Point(p.place["geometry"]["location"]["lat"], p.place["geometry"]["location"]["lng"])).miles
            })
        return ret
        