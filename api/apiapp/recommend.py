from flask import Blueprint, g, request, abort
from .auth import authenticate
from .location import Point
import requests, json
import psycopg
from dataclasses import dataclass

bp = Blueprint("recommend", __name__, url_prefix="/recommend")

@bp.route("", methods=["GET"])
@authenticate
def get_recommendations():
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
    radius = 20000.0
    if "rad" in request.args:
        try:
            radius = float(request.args["rad"] / 1609.344)
        except ValueError:
            pass
    res = requests.post("https://places.googleapis.com/v1/places:searchText", json={
        "textQuery": category,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": loc.lat,
                    "longitude": loc.lon
                },
                "radius": radius
            }
        }
        }, headers={
        "X-Goog-Api-Key": g.google_api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.types,places.formattedAddress,places.location"
    }).json()

    @dataclass
    class Recommendation:
        index: int
        place: dict
        visits: int
    places = []
    for c in res["places"]:
        places.append(Recommendation(len(places), c, 0))
    with g.conn.cursor() as cur:
        for c in places:
            cur.execute("SELECT COUNT(*) FROM places WHERE id = %s;", (c.place["id"],))
            count, = cur.fetchone()
            if (count == 0):
                cur.execute("INSERT INTO places(id, name, address, coords) VALUES (%s, %s, %s, %s);",
                            (c.place["id"], c.place["displayName"]["text"], c.place["formattedAddress"],
                             Point(c.place["location"]["latitude"], c.place["location"]["longitude"])))
                for t in c.place["types"]:
                    cur.execute("INSERT INTO placetypes(id, type) VALUES (%s, %s);", (c.place["id"], t))
        cur.execute("SELECT eventid FROM attendees WHERE userid = %s;", (g.userid,))
        events = []
        for row in cur:
            eid, = row
            events.append(eid)
        cur.execute("SELECT placeid, SUM(visits) FROM locations WHERE eventid = ANY(%s) GROUP BY placeid;", (events,))
        for row in cur:
            pid, visits = row
            for p in places:
                if p.place["id"] == pid:
                    p.visits = visits
                    break
        places.sort(key=lambda x: x.visits + x.index)
        ret = []
        for p in places:
            ret.append({
                "name": p.place["displayName"]["text"],
                "address": p.place["formattedAddress"],
                "location": {
                    "lat": p.place["location"]["latitude"],
                    "lon": p.place["location"]["longitude"]
                },
                "distance": loc.distanceto(Point(p.place["location"]["latitude"], p.place["location"]["longitude"])).miles
            })
        return ret
        