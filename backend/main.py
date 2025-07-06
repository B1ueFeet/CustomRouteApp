from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi.responses import Response

app = FastAPI()

# Permitir peticiones desde el frontend en dev
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

OSRM_URL = "http://localhost:5000/route/v1/driving/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

@app.get("/api/route")
async def get_route(coords: str = Query(...), overview: str = "full"):
    """
    coords: "lon1,lat1;lon2,lat2;..."
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
          f"{OSRM_URL}{coords}",
          params={"overview": overview, "geometries": "geojson"}
        )
        return r.json()

@app.get("/api/geocode")
async def geocode(q: str = Query(..., description="Texto a buscar")):
    async with httpx.AsyncClient() as client:
        r = await client.get(NOMINATIM_URL, params={"q": q, "format": "json"})
        return r.json()
