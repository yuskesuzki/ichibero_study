from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles

app = FastAPI()

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


app.mount("/", StaticFiles(directory="static"), name="static")
