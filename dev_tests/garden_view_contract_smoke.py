"""Isolated checks for the Planner consumers in Garden Control and Workspace."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    workspace = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="gardenhub-garden-views-") as temporary:
        os.environ["GARDENHUB_DB_PATH"] = str(Path(temporary) / "garden-views.db")

        from flask import Blueprint, Flask

        from gardenhub.db.connection import get_conn
        from gardenhub.db.initialization import init_all_tables
        from gardenhub.routes import automation_routes
        from gardenhub.services.overview import get_garden_snapshot
        from gardenhub.services.planner_layout import save_planner_layout
        from gardenhub.services.planner_projection import get_planner_projection

        init_all_tables()
        today = datetime.now(timezone.utc).date().isoformat()
        with get_conn() as connection:
            connection.executemany(
                "INSERT INTO zones (zone_id, name, active) VALUES (?, ?, ?)",
                [("north", "North beds", 1), ("south", "South beds", 1)],
            )
            connection.executemany(
                "INSERT INTO beds (bed_id, zone_id, active) VALUES (?, ?, ?)",
                [("raised-1", "north", 1), ("raised-2", "south", 1)],
            )
            connection.executemany(
                "INSERT INTO sensors (sensor_id, bed_id, sensor_type, active) VALUES (?, ?, ?, ?)",
                [
                    ("soil-1", "raised-1", "moisture", 1),
                    ("soil-2", "raised-2", "moisture", 0),
                ],
            )
            connection.execute(
                """INSERT INTO sensor_readings
                   (timestamp, date, bed_id, sensor_id, slot, moisture_raw, moisture_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f"{today}T09:00:00+00:00", today, "raised-1", "soil-1", 1, 540, 61),
            )
            connection.execute(
                """INSERT INTO watering_events
                   (timestamp, date, zone_id, bed_id, minutes, mode)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f"{today}T08:00:00+00:00", today, "north", "raised-1", 7, "auto"),
            )
            connection.commit()
        connection.close()

        layout = {
            "garden": {
                "name": "Projection garden",
                "width": 20,
                "height": 10,
                "measurement": "metric",
                "units": "m",
                "north": 37,
            },
            "objects": [
                {
                    "id": "bed-raised-1",
                    "kind": "bed",
                    "variant": "raised-bed",
                    "layer": "beds",
                    "name": "Kitchen bed",
                    "bedId": "raised-1",
                    "x": 2,
                    "y": 1,
                    "width": 5,
                    "height": 3,
                    "rotation": 0,
                    "z": 300,
                },
                {
                    "id": "bed-raised-2",
                    "kind": "bed",
                    "variant": "large-container",
                    "layer": "beds",
                    "name": "South container",
                    "bedId": "raised-2",
                    "x": 12,
                    "y": 5.5,
                    "width": 4,
                    "height": 2.5,
                    "rotation": 18,
                    "z": 301,
                },
                {
                    "id": "bed-unlinked",
                    "kind": "bed",
                    "variant": "ground-bed",
                    "layer": "beds",
                    "name": "Future bed",
                    "bedId": "not-a-domain-bed",
                    "x": 8,
                    "y": 1,
                    "width": 2,
                    "height": 2,
                    "rotation": 0,
                    "z": 302,
                },
                {
                    "id": "gravel-path",
                    "kind": "surface",
                    "variant": "gravel",
                    "layer": "paths",
                    "name": "Diagonal path",
                    "x": 4,
                    "y": 8,
                    "width": 12,
                    "height": 0.75,
                    "rotation": 12,
                    "z": 200,
                },
            ],
        }
        saved = save_planner_layout("local-garden", layout)
        garden = get_garden_snapshot()
        projection = get_planner_projection("local-garden", garden)

        assert projection["garden"] == saved["garden"]
        assert projection["dimensions_label"] == "20 × 10 m"
        assert projection["aspect_ratio"] == 2
        assert projection["bed_count"] == 3
        assert projection["linked_bed_count"] == 2
        assert [item["id"] for item in projection["objects"]] == [
            "gravel-path",
            "bed-raised-1",
            "bed-raised-2",
            "bed-unlinked",
        ]

        by_id = {item["id"]: item for item in projection["objects"]}
        assert by_id["bed-raised-1"]["left_pct"] == 10
        assert by_id["bed-raised-1"]["width_pct"] == 25
        assert by_id["bed-raised-1"]["operational"]["status"] == "healthy"
        assert by_id["bed-raised-1"]["operational"]["watering"]["minutes"] == 7
        assert by_id["bed-raised-2"]["rotation"] == 18
        assert by_id["bed-raised-2"]["operational"]["status_label"] == "Sensor offline"
        assert by_id["bed-unlinked"]["operational"] is None
        assert by_id["gravel-path"]["operational"] is None

        app = Flask(__name__, root_path=str(workspace), template_folder=str(workspace / "templates"))
        planner_stub = Blueprint("planner", __name__)

        @planner_stub.route("/planner")
        def planner():
            return "planner"

        app.register_blueprint(planner_stub)
        with app.test_request_context("/"):
            template = app.jinja_env.get_template("components/garden_snapshot.html")
            snapshot = template.module.garden_snapshot(projection)
            empty_snapshot = template.module.garden_snapshot(None)

        assert snapshot.count("data-bed-select=") == 2
        assert 'class="garden-snapshot__viewport"' in snapshot
        assert "--object-x: 10.0%" in snapshot
        assert "--object-rotation: 18.0deg" in snapshot
        assert "--north-rotation: 37.0deg" in snapshot
        assert "Last watered 7 min" in snapshot
        assert "Future bed, contextual bed" in snapshot
        assert "draggable" not in snapshot
        assert "Open Planner" in empty_snapshot

        snapshot_css = (workspace / "static" / "css" / "garden-control.css").read_text(
            encoding="utf-8"
        )
        assert "container-type: size" in snapshot_css
        assert "100cqh * var(--garden-aspect)" in snapshot_css
        assert "100cqw / var(--garden-aspect)" in snapshot_css

        captured = {}

        def capture_template(template_name, **context):
            captured.update(template_name=template_name, **context)
            return "rendered"

        original_render_template = automation_routes.render_template
        automation_routes.render_template = capture_template
        try:
            with app.test_request_context("/automation"):
                assert automation_routes.automation() == "rendered"
        finally:
            automation_routes.render_template = original_render_template
        assert captured["template_name"] == "automation.html"
        assert captured["planner_projection"]["garden"]["north"] == 37

        print("Garden view contract smoke passed")
        import gc

        gc.collect()


if __name__ == "__main__":
    main()
