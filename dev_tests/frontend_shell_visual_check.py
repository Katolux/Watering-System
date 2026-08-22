"""Run the browser smoke against isolated saved and empty databases.

Usage: ``python dev_tests/frontend_shell_visual_check.py``. Playwright is resolved
from the project, a bundled Codex runtime, or ``PLAYWRIGHT_MODULE_PATH``; a browser
can be selected with ``PLAYWRIGHT_BROWSER_CHANNEL`` or ``PLAYWRIGHT_BROWSER_PATH``.
"""

import gc
import logging
import os
import socket
import subprocess
import sys
import tempfile
import threading
from datetime import date
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))


def _prepare_database(database: Path, *, saved_plan: bool) -> None:
    os.environ["GARDENHUB_DB_PATH"] = str(database)

    from gardenhub.db.connection import get_conn
    from gardenhub.db.initialization import init_all_tables
    from gardenhub.repositories.weather_repo import save_weather_record
    from gardenhub.services.planner_layout import save_planner_layout
    from seeding.plant_seeder import seed_from_file

    init_all_tables()
    seed_from_file(WORKSPACE / "plants" / "tomato.json")
    save_weather_record({
        "date": date.today().isoformat(),
        "temp_max": 24,
        "temp_min": 13,
        "precipitation": 0,
        "sunshine": 8,
        "daylight": 12,
        "wind_max": 9,
        "wind_dir": 180,
        "weather_code": 1,
    })

    with get_conn() as connection:
        connection.execute(
            "INSERT INTO zones (zone_id, name, active) VALUES (?, ?, ?)",
            ("smoke-zone", "Smoke test zone", 1),
        )
        connection.execute(
            "INSERT INTO beds (bed_id, zone_id, active) VALUES (?, ?, ?)",
            ("raised-1", "smoke-zone", 1),
        )
        connection.execute(
            "INSERT INTO sensors (sensor_id, bed_id, sensor_type, active) VALUES (?, ?, ?, ?)",
            ("smoke-sensor", "raised-1", "moisture", 1),
        )
        connection.commit()

    if saved_plan:
        save_planner_layout("local-garden", {
            "version": 1,
            "garden": {
                "name": "Browser smoke garden",
                "width": 12,
                "height": 8,
                "measurement": "metric",
                "units": "m",
                "north": 27,
            },
            "objects": [
                {
                    "id": "smoke-path",
                    "kind": "surface",
                    "variant": "gravel",
                    "layer": "paths",
                    "name": "Smoke gravel path",
                    "x": 1,
                    "y": 6,
                    "width": 9,
                    "height": 0.8,
                    "rotation": 4,
                    "z": 200,
                },
                {
                    "id": "smoke-linked-bed",
                    "kind": "bed",
                    "variant": "raised-bed",
                    "layer": "beds",
                    "name": "Smoke linked bed",
                    "bedId": "raised-1",
                    "x": 1.5,
                    "y": 1.2,
                    "width": 4,
                    "height": 2.5,
                    "rotation": 0,
                    "z": 300,
                },
                {
                    "id": "smoke-tomatoes",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Smoke tomatoes",
                    "plantId": "tomato",
                    "bedId": "raised-1",
                    "quantity": 6,
                    "x": 2,
                    "y": 1.5,
                    "width": 2,
                    "height": 1.5,
                    "rotation": 0,
                    "z": 600,
                },
                {
                    "id": "smoke-missing-plant",
                    "kind": "plant",
                    "layer": "plants",
                    "name": "Retired smoke plant",
                    "plantId": "retired-smoke-plant",
                    "quantity": 3,
                    "x": 7,
                    "y": 2,
                    "width": 1.5,
                    "height": 1.5,
                    "rotation": 12,
                    "z": 601,
                },
            ],
        })


def _assert_port_released(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as check:
        check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        check.bind(("127.0.0.1", port))


def _run_state(app, database: Path, *, saved_plan: bool) -> None:
    from werkzeug.serving import make_server

    _prepare_database(database, saved_plan=saved_plan)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        environment = os.environ.copy()
        environment["FRONTEND_SMOKE_BASE_URL"] = f"http://127.0.0.1:{port}"
        environment["FRONTEND_SMOKE_EXPECT_SAVED"] = "1" if saved_plan else "0"
        subprocess.run(
            ["node", str(WORKSPACE / "dev_tests" / "frontend_shell_visual_check.cjs")],
            cwd=WORKSPACE,
            env=environment,
            check=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        gc.collect()
        _assert_port_released(port)


def main() -> None:
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory(prefix="gardenhub-frontend-smoke-") as temporary:
        temporary_path = Path(temporary)
        try:
            _prepare_database(temporary_path / "bootstrap.db", saved_plan=True)

            from app import app

            _run_state(app, temporary_path / "saved.db", saved_plan=True)
            _run_state(app, temporary_path / "empty.db", saved_plan=False)
        finally:
            gc.collect()

    print("Frontend browser smoke check passed (saved and empty Planner states)")


if __name__ == "__main__":
    main()
