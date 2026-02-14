from flask import Blueprint, request, jsonify
from repositories import next_slot_for_today, save_reading
from calibration import OUT_OF_SOIL_RAW

receiver_bp = Blueprint("receiver", __name__)


@receiver_bp.route("/sensor_data", methods=["POST"])
def receive_soil():
    data = request.get_json(silent=True) or {}

    bed_id = data.get("bed")
    sensor_id = data.get("sensor")
    moisture = data.get("moisture")

    # --- validation ---
    if bed_id is None or sensor_id is None or moisture is None:
        return jsonify({
            "status": "error",
            "error": "Missing bed, sensor or moisture"
        }), 400

    try:
        moisture = int(moisture)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "error": "moisture must be an integer"
        }), 400
    # Ignore invalid "air/unplugged" readings
    if moisture >= OUT_OF_SOIL_RAW:
        print(f"[SENSOR] ignored (out_of_soil) | bed={bed_id} | sensor={sensor_id} | raw={moisture}")
        return jsonify({"status": "ignored", "reason": "out_of_soil"}), 202

    

    # --- repository calls (DB handled there) ---
    slot = next_slot_for_today(bed_id)
    if slot is None:
        return jsonify({
           "status": "error",
           "error": "All 6 slots for today are already filled for this bed"
         }), 409


    save_reading(
        bed_id=bed_id,
        sensor_id=sensor_id,
        slot=slot,
        moisture_raw=moisture
    )

    # --- debug log ---
    print(
        f"[SENSOR] saved | "
        f"bed={bed_id} | "
        f"sensor={sensor_id} | "
        f"slot={slot} | "
        f"moisture={moisture}"
    )

    return jsonify({"status": "ok"}), 200
