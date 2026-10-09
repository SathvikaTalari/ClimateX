import math
import requests
from PIL import Image
from io import BytesIO

def fetch_esri_basemap(bounds, w, h):
    min_lon, min_lat, max_lon, max_lat = bounds
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2
    
    # Calculate exact zoom level so that the bounding box fits in our 2x2 grid (512x512)
    # Actually, if we just do:
    max_diff = max(max_lon - min_lon, max_lat - min_lat)
    zoom = int(math.log2(360.0 / max_diff)) + 1
    zoom = min(17, zoom)

    lat_rad = math.radians(center_lat)
    n = 2.0 ** zoom
    x_center = (center_lon + 180.0) / 360.0 * n
    y_center = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

    # We need the tiles that cover the bounding box
    n_min_x = ((min_lon + 180.0) / 360.0 * n)
    n_max_x = ((max_lon + 180.0) / 360.0 * n)
    lat_rad_max = math.radians(max_lat)
    lat_rad_min = math.radians(min_lat)
    n_min_y = ((1.0 - math.asinh(math.tan(lat_rad_max)) / math.pi) / 2.0 * n)
    n_max_y = ((1.0 - math.asinh(math.tan(lat_rad_min)) / math.pi) / 2.0 * n)

    tx_min, tx_max = int(math.floor(n_min_x)), int(math.floor(n_max_x))
    ty_min, ty_max = int(math.floor(n_min_y)), int(math.floor(n_max_y))

    # To avoid fetching too many tiles, limit to a small grid (e.g. max 3x3)
    if tx_max - tx_min > 3: tx_max = tx_min + 3
    if ty_max - ty_min > 3: ty_max = ty_min + 3

    grid_w = (tx_max - tx_min + 1) * 256
    grid_h = (ty_max - ty_min + 1) * 256
    stitched = Image.new("RGBA", (grid_w, grid_h))
    
    session = requests.Session()
    session.headers.update({"User-Agent": "ClimateX/1.0"})
    
    for tx in range(tx_min, tx_max + 1):
        for ty in range(ty_min, ty_max + 1):
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}"
            try:
                r = session.get(url, timeout=5)
                if r.status_code == 200:
                    tile = Image.open(BytesIO(r.content)).convert("RGBA")
                    stitched.paste(tile, ((tx - tx_min) * 256, (ty - ty_min) * 256))
                else:
                    print(f"Failed to fetch {url}: {r.status_code}")
            except Exception as e:
                print(e)

    # Pixel coords of the bounding box relative to stitched image
    px_min_lon = n_min_x * 256
    px_max_lon = n_max_x * 256
    px_min_lat = n_max_y * 256
    px_max_lat = n_min_y * 256

    crop_left = px_min_lon - (tx_min * 256)
    crop_right = px_max_lon - (tx_min * 256)
    crop_top = px_max_lat - (ty_min * 256)
    crop_bottom = px_min_lat - (ty_min * 256)
    
    print(f"Crop: {crop_left}, {crop_top}, {crop_right}, {crop_bottom}")
    cropped = stitched.crop((int(crop_left), int(crop_top), int(crop_right), int(crop_bottom)))
    return cropped.resize((w, h))

if __name__ == "__main__":
    bounds = (-122.4194, 37.7749, -122.3194, 37.8749)
    img = fetch_esri_basemap(bounds, 500, 500)
    img.save("test_sat.png")
    print("Saved test_sat.png")
