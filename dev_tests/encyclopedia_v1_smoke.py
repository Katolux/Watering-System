"""Focused smoke checks for the shared Encyclopedia v1 plant detail views."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402


TAB_EXPECTATIONS = {
    "overview": "At a glance",
    "growing-guide": "How to grow Tomato",
    "calendar": "The gardening year",
    "companions": "Companion planting",
    "pests-diseases": "Pests &amp; diseases",
    "soil-fertilisation": "Build healthy growth",
    "harvest-storage": "From garden to kitchen",
}


def main():
    client = app.test_client()

    for tab, expected in TAB_EXPECTATIONS.items():
        response = client.get(f"/automation/plants/tomato?tab={tab}")
        assert response.status_code == 200, (tab, response.status_code)
        html = response.get_data(as_text=True)
        assert expected in html, (tab, expected)
        assert 'aria-current="page"' in html

    overview = client.get("/automation/plants/tomato?tab=overview").get_data(as_text=True)
    for asset in (
        "images/botanical/planner/tomato.png",
        "images/encyclopedia/tomato-growth-habit.png",
        "images/encyclopedia/tomato-mature-size.png",
    ):
        assert asset in overview, asset
    for unwanted in ("Mixed", "Visual guide", "Difficulty in your area", "Heirloom"):
        assert unwanted not in overview, unwanted

    calendar = client.get("/automation/plants/tomato?tab=calendar").get_data(as_text=True)
    assert "Not recommended" in calendar
    assert "Direct sowing is generally not recommended" in calendar

    for asset_url in (
        "/static/images/botanical/planner/tomato.png?v=2",
        "/static/images/encyclopedia/tomato-growth-habit.png?v=2",
        "/static/images/encyclopedia/tomato-mature-size.png?v=2",
    ):
        assert client.get(asset_url).status_code == 200, asset_url

    print("Encyclopedia v1 smoke checks passed.")


if __name__ == "__main__":
    main()
