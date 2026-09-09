"""Isolated smoke coverage for the Planner layout persistence contract."""

import gc
import json
import os
import tempfile
from pathlib import Path


def main():
    workspace = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="gardenhub-planner-") as temporary:
        database = Path(temporary) / "planner-smoke.db"
        os.environ["GARDENHUB_DB_PATH"] = str(database)

        from flask import Flask

        from gardenhub.db.initialization import init_all_tables
        from gardenhub.routes.planner_routes import planner_bp
        from gardenhub.services.garden_context import get_garden_context
        from gardenhub.services.overview import get_planner_state

        init_all_tables()
        app = Flask(__name__, root_path=str(workspace))
        app.register_blueprint(planner_bp)
        client = app.test_client()

        empty = client.get("/api/planner/layout").get_json()
        assert empty["planExists"] is False
        assert get_planner_state(garden_context=get_garden_context(False))["objects"] == []

        layout = {
            "version": 1,
            "garden": {
                "name": "Persistence smoke garden",
                "width": 12,
                "height": 9,
                "measurement": "metric",
                "units": "m",
                "north": 37,
            },
            "objects": [
                {
                    "id": "surface-smoke-1",
                    "kind": "surface",
                    "variant": "soil",
                    "layer": "surfaces",
                    "name": "Scaled soil",
                    "locked": True,
                    "x": 1.25,
                    "y": 2.5,
                    "width": 4.5,
                    "height": 3.25,
                    "rotation": 28,
                    "z": 101,
                },
                {
                    "id": "plant-smoke-1",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Tomato group",
                    "locked": False,
                    "plantId": "tomato",
                    "bedId": "bed-1",
                    "sourcePlantingId": 42,
                    "quantity": 6,
                    "x": 3,
                    "y": 1,
                    "width": 1.5,
                    "height": 2,
                    "rotation": 15,
                    "z": 600,
                },
                {
                    "id": "plant-missing-1",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Heritage plant group",
                    "plantId": "retired-catalogue-plant",
                    "bedId": "bed-legacy",
                    "quantity": 7,
                    "x": 5,
                    "y": 5,
                    "width": 1.2,
                    "height": 1.4,
                    "rotation": 5,
                    "z": 601,
                },
                {
                    "id": "plant-missing-without-quantity",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Unknown historical group",
                    "plantId": "removed-without-history",
                    "x": 7,
                    "y": 5,
                    "width": 1,
                    "height": 1,
                    "rotation": 0,
                    "z": 602,
                },
                {
                    "id": "surface-smoke-copy",
                    "kind": "surface",
                    "variant": "soil",
                    "layer": "surfaces",
                    "name": "Scaled soil copy",
                    "x": 6,
                    "y": 2.5,
                    "width": 3,
                    "height": 2,
                    "rotation": 28,
                    "z": 99,
                },
            ],
        }

        response = client.put("/api/planner/layout", json=layout)
        assert response.status_code == 200, response.get_data(as_text=True)
        saved = response.get_json()
        assert saved["ok"] is True
        assert saved["gardenId"] == "local-garden"

        response = client.get("/api/planner/layout")
        loaded = response.get_json()
        assert response.status_code == 200
        assert loaded["planExists"] is True
        assert loaded["garden"]["north"] == 37
        assert loaded["objects"] == saved["objects"]
        assert loaded["objects"][0]["locked"] is True
        assert loaded["objects"][1]["locked"] is False
        assert "locked" not in loaded["objects"][2]
        assert [item["z"] for item in loaded["objects"]] == [101, 600, 601, 602, 99]

        from gardenhub.db.connection import get_conn

        with get_conn() as connection:
            assert connection.execute("SELECT COUNT(*) FROM planner_layouts").fetchone()[0] == 1
            assert connection.execute("SELECT COUNT(*) FROM bed_plantings").fetchone()[0] == 0
        connection.close()

        repeated = client.put("/api/planner/layout", json=layout)
        assert repeated.status_code == 200
        assert len(client.get("/api/planner/layout").get_json()["objects"]) == 5

        state = get_planner_state(garden_context=get_garden_context(False))
        assert state["planExists"] is True
        assert state["persistence"] == "backend"
        assert state["objects"] == saved["objects"]

        updated = json.loads(json.dumps(layout))
        updated["objects"].pop()
        updated["objects"][0]["x"] = 2.75
        response = client.put("/api/planner/layout", json=updated)
        assert response.status_code == 200
        loaded = client.get("/api/planner/layout").get_json()
        assert len(loaded["objects"]) == 4
        assert loaded["objects"][0]["x"] == 2.75
        missing = next(item for item in loaded["objects"] if item["id"] == "plant-missing-1")
        assert missing["plantId"] == "retired-catalogue-plant"
        assert missing["bedId"] == "bed-legacy"
        assert missing["quantity"] == 7
        missing_without_quantity = next(
            item for item in loaded["objects"]
            if item["id"] == "plant-missing-without-quantity"
        )
        assert "quantity" not in missing_without_quantity

        invalid = json.loads(json.dumps(updated))
        invalid["objects"][0]["width"] = 1000
        response = client.put("/api/planner/layout", json=invalid)
        assert response.status_code == 400
        assert response.get_json()["ok"] is False
        loaded_after_failure = client.get("/api/planner/layout").get_json()
        assert loaded_after_failure["objects"] == loaded["objects"]

        for invalid_lock in ("true", 1, None):
            invalid = json.loads(json.dumps(updated))
            invalid["objects"][0]["locked"] = invalid_lock
            response = client.put("/api/planner/layout", json=invalid)
            assert response.status_code == 400
        assert client.get("/api/planner/layout").get_json()["objects"] == loaded["objects"]

        updated["objects"][0]["locked"] = False
        assert client.put("/api/planner/layout", json=updated).status_code == 200
        assert client.get("/api/planner/layout").get_json()["objects"][0]["locked"] is False
        geometry_layout = json.loads(json.dumps(layout))
        geometry_layout["objects"] = [
            {
                "id": "geometry-area",
                "kind": "surface",
                "variant": "grass",
                "layer": "surfaces",
                "name": "Editable grass",
                "x": 1,
                "y": 1,
                "width": 4,
                "height": 3,
                "rotation": 25,
                "z": 100,
                "geometryType": "area",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 1, "y": 0},
                    {"x": 0.75, "y": 0.6},
                    {"x": 0.5, "y": 1},
                    {"x": 0, "y": 1},
                ],
            },
            {
                "id": "geometry-path",
                "kind": "structure",
                "variant": "fence",
                "layer": "structures",
                "name": "Editable fence",
                "x": 6,
                "y": 2,
                "width": 4,
                "height": 3,
                "rotation": 0,
                "z": 500,
                "geometryType": "path",
                "points": [
                    {"x": 0, "y": 0.5},
                    {"x": 0.5, "y": 0.5},
                    {"x": 1, "y": 1},
                ],
            },
        ]

        response = client.put("/api/planner/layout", json=geometry_layout)
        assert response.status_code == 200, response.get_data(as_text=True)
        geometry_saved = response.get_json()["objects"]
        assert geometry_saved == geometry_layout["objects"]
        assert client.get("/api/planner/layout").get_json()["objects"] == geometry_saved
        assert get_planner_state(
            garden_context=get_garden_context(False)
        )["objects"] == geometry_saved

        from gardenhub.services.planner_projection import get_planner_projection

        projection = get_planner_projection("local-garden", {"beds": []})
        assert [item["points"] for item in projection["objects"]] == [
            item["points"] for item in geometry_saved
        ]

        invalid_cases = [
            ("geometryType", "curve"),
            ("geometryType", []),
            ("points", [{"x": 0, "y": 0}]),
            ("points", [{"x": 0, "y": 0}] * 129),
            ("points", [{"x": True, "y": 0}] * 3),
            ("points", [{"x": 2, "y": 0}] * 3),
            ("points", [{"x": 0, "y": 0}] * 3),
        ]
        for field, value in invalid_cases:
            bad_geometry = json.loads(json.dumps(geometry_layout))
            bad_geometry["objects"][0][field] = value
            response = client.put("/api/planner/layout", json=bad_geometry)
            assert response.status_code == 400
            assert client.get(
                "/api/planner/layout"
            ).get_json()["objects"] == geometry_saved
                
        print("Planner persistence smoke passed")
        gc.collect()


if __name__ == "__main__":
    main()
