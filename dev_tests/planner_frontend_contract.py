"""Run the Planner frontend contract against an isolated database and server."""

import gc
import os
import subprocess
import tempfile
import threading
from datetime import date
from pathlib import Path


def main():
    workspace = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="gardenhub-planner-frontend-") as temporary:
        os.environ["GARDENHUB_DB_PATH"] = str(Path(temporary) / "planner-frontend.db")

        from gardenhub.db.initialization import init_all_tables
        from gardenhub.repositories.weather_repo import save_weather_record
        from gardenhub.services.planner_layout import save_planner_layout
        from seeding.plant_seeder import seed_from_file

        init_all_tables()
        seed_from_file(workspace / "plants" / "tomato.json")
        save_weather_record({
            "date": date.today().isoformat(),
            "temp_max": 20,
            "temp_min": 10,
            "precipitation": 0,
            "sunshine": 8,
            "daylight": 12,
            "wind_max": 5,
            "wind_dir": 180,
            "weather_code": 0,
        })
        save_planner_layout("local-garden", {
            "version": 1,
            "garden": {
                "name": "Planner contract garden",
                "width": 10,
                "height": 8,
                "measurement": "metric",
                "units": "m",
                "north": 0,
            },
            "objects": [
                {
                    "id": "plant-valid",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Tomato group",
                    "plantId": "tomato",
                    "quantity": 999,
                    "x": 1,
                    "y": 1,
                    "width": 1,
                    "height": 1.6,
                    "rotation": 0,
                    "z": 600,
                },
                {
                    "id": "plant-missing",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Heritage tomato row",
                    "plantId": "retired-tomato",
                    "bedId": "legacy-bed",
                    "quantity": 7,
                    "x": 3,
                    "y": 1,
                    "width": 1.5,
                    "height": 1,
                    "rotation": 12,
                    "z": 601,
                },
                {
                    "id": "plant-missing-no-quantity",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Unknown historical group",
                    "plantId": "removed-without-history",
                    "x": 5,
                    "y": 1,
                    "width": 1,
                    "height": 1,
                    "rotation": 0,
                    "z": 602,
                },
            ],
        })

        from app import app
        from werkzeug.serving import make_server

        server = make_server("127.0.0.1", 0, app, threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            environment = os.environ.copy()
            environment["PLANNER_TEST_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
            subprocess.run(
                ["node", str(workspace / "dev_tests" / "planner_frontend_contract.cjs")],
                cwd=workspace,
                env=environment,
                check=True,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            gc.collect()


if __name__ == "__main__":
    main()
