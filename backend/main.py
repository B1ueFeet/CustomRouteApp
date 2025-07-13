from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        
    allow_credentials=True,     
    allow_methods=["*"],
    allow_headers=["*"],
)

OSRM_URL = os.environ["OSRM_URL"]
NOMINATIM_URL = os.environ["NOMINATIM_URL"]


@app.get("/api/route")
async def get_route(
    coords: str = Query(..., description="lon1,lat1;lon2,lat2;..."),
    overview: str = Query("full", description="full|simplified"),
    steps: bool = Query(False, description="include turn-by-turn instructions")
):
    """
    coords: "lon1,lat1;lon2,lat2;..."
    overview: "full" or "simplified"
    steps: whether to include steps
    """
    params = {
        "overview": overview,
        "geometries": "geojson",
        "steps": "true" if steps else "false"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{OSRM_URL}{coords}", params=params)
        r.raise_for_status()
        return r.json()


@app.get("/api/geocode")
async def geocode(q: str = Query(..., description="search text")):
    async with httpx.AsyncClient() as client:
        r = await client.get(NOMINATIM_URL, params={"q": q, "format": "json"})
        r.raise_for_status()
        return r.json()
