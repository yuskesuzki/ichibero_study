from fastapi import FastAPI, Response, Depends
from fastapi.staticfiles import StaticFiles
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles
import psycopg2
import psycopg2.pool
import json

from app.models import PointsOfMapCreate, PointsOfMapUpdate
# from app.model import PoiCreate, PoiUpdate


app = FastAPI()

pool = psycopg2.pool.SimpleConnectionPool(
    dsn="postgresql://postgres:postgres@postgis:5432/postgres",
    minconn=2,
    maxconn=4
)

def get_connection():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/zelda_totk_ground.png")
async def make_image():
    with Reader("static/zelda_totk_ground_cog.tif") as src:
        img = src.read([1, 2, 3]) # band-1,2,3

    png = img.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")

@app.get("/zelda_totk_ground_cog_part.png")
async def make_image_remote_cog_part(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    max_size: int = 256
):
    with Reader(
        "http://fileserver/zelda_totk_ground_cog.tif"
    ) as image:
        imgdata = image.part(
            bbox=(minx, miny, maxx, maxy),
            indexes = (1, 2, 3),
            dst_crs = "EPSG:6674",
            max_size=max_size,
        )
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")

@app.get("/tiles/{z}/{x}/{y}.png")
async def make_image_remote_cog_tile(
    z: int,
    x: int,
    y: int,
):
    print(f"tile: {z}/{x}/{y}")
    with Reader(
        "http://fileserver/zelda_totk_ground_cog.tif"
    ) as image:
        print(image)
        imgdata = image.tile(
            x,
            y,
            z,
            indexes = (1, 2, 3),
            resampling_method="bilinear",
            tilesize=256,
        )
        png = imgdata.render(img_format="PNG", **img_profiles.get("png"))
    return Response(png, media_type="image/png")

@app.get("/pois")
# async def get_pois(conn=Depends(get_connection)):
def get_pois(conn=Depends(get_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT ST_AsGeoJSON(poi.*) FROM points_of_map AS poi")
        pois = cur.fetchall()

    features = [json.loads(row[0]) for row in pois]
    return {"type": "FeatureCollection", "features": features}

@app.get("/pois_sql2")
def get_pois_sql2(bbox: str, conn=Depends(get_connection)):

    # query parameter bbox values validate
    _bbox = bbox.split(",")
    if len(_bbox) != 4:
        raise ValueError("bbox must be a comma-separated list of four values")

    minx, miny, maxx, maxy = list(map(float, _bbox))

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ST_AsGeoJSON(poi.*) FROM points_of_map AS poi
            WHERE geom && ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, 4326)
            LIMIT 1000
            """,
            {
                "minx": minx,
                "miny": miny,
                "maxx": maxx,
                "maxy": maxy
            },
        )
        pois = cur.fetchall()

    features = [json.loads(row[0]) for row in pois]
    return {"type": "FeatureCollection", "features": features}


@app.post("/pois")
def create_poi(data:PointsOfMapCreate, conn=Depends(get_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO points_of_map (name, level, poi_type, geom, description)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
            """,
            (data.name, data.level, data.poi_type, data.latitude, data.longitude, data.description),
        )
        conn.commit()

        # Get the ID of the newly created POI
        cur.execute("SELECT lastval() FROM points_of_map")
        res = cur.fetchone()
        poi_id = res[0]
    return {"id": poi_id}

@app.delete("/pois/{poi_id}")
def delete_poi(poi_id: int, conn=Depends(get_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM points_of_map WHERE id = %s
            """,
            (poi_id,),
        )
        conn.commit()
    return Response(status_code=204)

@app.patch("/pois/{poi_id}")
def update_poi(poi_id: int, data: PointsOfMapUpdate, conn=Depends(get_connection)):
    with conn.cursor() as cur:
        # Check target poi exists
        cur.execute(
            """
            SELECT id FROM points_of_map WHERE id = %s
            """,
            (poi_id,),
        )
        res = cur.fetchone()
        if res is None:
            return Response(status_code=404)

        # # Build the update query dynamically based on the provided fields
        set_clause = []
        params = []

        if data.name is not None:
            set_clause.append("name = %s")
            params.append(data.name)
        if data.level is not None:
            set_clause.append("level = %s")
            params.append(data.level)
        if data.poi_type is not None:
            set_clause.append("poi_type = %s")
            params.append(data.poi_type)
        if data.latitude is not None and data.longitude is not None:
            set_clause.append(
                "geom = ST_SetSRID(" \
                "ST_MakePoint(" \
                "    COALESCE(%s, ST_X(geom)), COALESCE(%s, ST_Y(geom))" \
                "), 4326)"
                )
            params.extend([data.latitude, data.longitude])
        if data.description is not None:
            set_clause.append("description = %s")
            params.append(data.description)

        # Join the set clause with commas
        set_clause_str = ", ".join(set_clause)

        # Add the ID to the parameters
        params.append(poi_id)

        # Execute the update query
        cur.execute(
            f"UPDATE points_of_map SET {set_clause_str} WHERE id = %s",
            tuple(params),
        )
        conn.commit()

    return {"status": "updated"}


# mount static files
app.mount("/", StaticFiles(directory="static"), name="static")
