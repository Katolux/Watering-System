import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


LOCALITY_FIELDS = (
    "city",
    "town",
    "village",
    "municipality",
    "hamlet",
    "locality",
    "suburb",
    "neighbourhood",
    "isolated_dwelling",
)

REGION_FIELDS = (
    "state",
    "region",
    "province",
)


def _first_address_value(address, fields):
    for field in fields:
        value = address.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def short_location_label(item):
    """Build a compact UI label from structured Nominatim address fields."""

    address = item.get("address") or {}
    locality = _first_address_value(address, LOCALITY_FIELDS)
    region = _first_address_value(address, REGION_FIELDS)

    if locality and region:
        return f"{locality}, {region}"
    if locality:
        return locality
    if region:
        return region

    display_name = item.get("display_name")
    if display_name is not None and str(display_name).strip():
        return str(display_name).strip()
    return "Selected garden location"


def search_location(query):
    """Search OpenStreetMap for a garden location."""

    query = (query or "").strip()

    if not query:
        return []

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 5,
        },
        headers={
            "User-Agent": "GardenHub/1.0",
        },
        timeout=10,
    )

    response.raise_for_status()

    results = []

    for item in response.json():
        results.append({
            "label": short_location_label(item),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
        })

    return results

def resolve_timezone(latitude, longitude):
    """Resolve the local timezone for coordinates using Open-Meteo."""

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    timezone_name = data.get("timezone")

    if not timezone_name:
        raise ValueError("Timezone could not be resolved.")

    return timezone_name
