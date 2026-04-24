import hashlib
import math
from typing import Iterable

import requests
from django.conf import settings

AVERAGE_SPEED_MPH = 60


KNOWN_COORDINATES = {
    "atlanta, ga": (33.7490, -84.3880),
    "chicago, il": (41.8781, -87.6298),
    "dallas, tx": (32.7767, -96.7970),
    "denver, co": (39.7392, -104.9903),
    "houston, tx": (29.7604, -95.3698),
    "los angeles, ca": (34.0522, -118.2437),
    "miami, fl": (25.7617, -80.1918),
    "new york, ny": (40.7128, -74.0060),
    "phoenix, az": (33.4484, -112.0740),
    "st. louis, mo": (38.6270, -90.1994),
    "san francisco, ca": (37.7749, -122.4194),
    "seattle, wa": (47.6062, -122.3321),
}


def build_route(current_location: str, pickup_location: str, dropoff_location: str) -> dict:
    locations = [current_location, pickup_location, dropoff_location]
    if settings.MAPBOX_ACCESS_TOKEN:
        try:
            return _build_mapbox_route(locations)
        except requests.RequestException:
            pass

    return _build_fallback_route(locations)


def interpolate_path(points: list[tuple[float, float]], steps_per_leg: int = 18) -> list[list[float]]:
    path: list[list[float]] = []
    for start, end in zip(points, points[1:]):
        for index in range(steps_per_leg):
            t = index / steps_per_leg
            lat = start[0] + (end[0] - start[0]) * t
            lng = start[1] + (end[1] - start[1]) * t
            path.append([round(lat, 6), round(lng, 6)])
    path.append([round(points[-1][0], 6), round(points[-1][1], 6)])
    return path


def coordinate_at_fraction(path: list[list[float]], fraction: float) -> list[float]:
    if not path:
        return [0, 0]
    clamped = max(0, min(1, fraction))
    index = min(len(path) - 1, round(clamped * (len(path) - 1)))
    return path[index]


def _build_mapbox_route(locations: Iterable[str]) -> dict:
    coords = [_mapbox_geocode(location) for location in locations]
    coord_param = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coord_param}"
    response = requests.get(
        url,
        params={
            "geometries": "geojson",
            "overview": "full",
            "access_token": settings.MAPBOX_ACCESS_TOKEN,
        },
        timeout=12,
    )
    response.raise_for_status()
    route = response.json()["routes"][0]
    path = [[lat, lng] for lng, lat in route["geometry"]["coordinates"]]
    distance_miles = route["distance"] / 1609.344
    duration_hours = route["duration"] / 3600
    return {
        "provider": "mapbox",
        "distance_miles": round(distance_miles, 1),
        "duration_hours": round(duration_hours, 2),
        "path": path,
    }


def _mapbox_geocode(location: str) -> tuple[float, float]:
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
    response = requests.get(
        url,
        params={"limit": 1, "access_token": settings.MAPBOX_ACCESS_TOKEN},
        timeout=12,
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise requests.RequestException(f"No geocode result for {location}")
    lng, lat = features[0]["center"]
    return lat, lng


def _build_fallback_route(locations: list[str]) -> dict:
    coords = [_fallback_coordinate(location) for location in locations]
    distance_miles = sum(_haversine_miles(start, end) for start, end in zip(coords, coords[1:]))
    road_adjusted_distance = distance_miles * 1.18
    return {
        "provider": "generated-demo-route",
        "distance_miles": round(road_adjusted_distance, 1),
        "duration_hours": round(road_adjusted_distance / AVERAGE_SPEED_MPH, 2),
        "path": interpolate_path(coords),
    }


def _fallback_coordinate(location: str) -> tuple[float, float]:
    normalized = location.strip().lower()
    if normalized in KNOWN_COORDINATES:
        return KNOWN_COORDINATES[normalized]

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    lat_seed = int(digest[:8], 16) / 0xFFFFFFFF
    lng_seed = int(digest[8:16], 16) / 0xFFFFFFFF
    lat = 25 + lat_seed * 23
    lng = -124 + lng_seed * 57
    return lat, lng


def _haversine_miles(start: tuple[float, float], end: tuple[float, float]) -> float:
    radius_miles = 3958.8
    lat1, lon1 = map(math.radians, start)
    lat2, lon2 = map(math.radians, end)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return radius_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

