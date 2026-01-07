from flask import Blueprint, request, jsonify
from db import get_conn
from repositories import next_slot_for_today, save_reading

receiver_bp = Blueprint("receiver", __name__)


@receiver_bp.route("/sensor_data", methods=["POST"])
def receive_soil():
    data = request.get_json(silent=True) or {}

    bed_id = data.get("bed")
    sensor_id = data.get("sensor")
    moisture = data.get("moisture")

    # --- validation ---
    if sensor_id is None or moisture is None:
        return jsonify({
            "status": "error",
            "error": "Missing sensor or moisture"
        }), 400

    try:
        moisture = int(moisture)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "error": "moisture must be an integer"
        }), 400

    # --- database operation ---
    with get_conn() as conn:
        slot = next_slot_for_today(conn, bed_id)
        save_reading(
            conn=conn,
            bed_id=bed_id,
            sensor_id=sensor_id,
            slot=slot,
            moisture_raw=moisture
        )
        conn.commit()

    # --- debug log ---
    print(
        f"[SENSOR] saved | "
        f"bed={bed_id} | "
        f"sensor={sensor_id} | "
        f"slot={slot} | "
        f"moisture={moisture}"
    )

    return jsonify({"status": "ok"}), 200
