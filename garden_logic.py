


def moisture_status(value, min_m, max_m):
    if value is None:
        return "N/A"
    if min_m is None or max_m is None:
        return "UNKNOWN"
    if value < min_m:
        return "LOW"
    if value > max_m:
        return "HIGH"
    return "OK"

def overall_bed_status(slot_statuses):
    statuses = [s["status"] for s in slot_statuses.values()]

    if all(s == "N/A" for s in statuses):
        return "NO DATA"

    if "LOW" in statuses:
        return "NEEDS WATER"

    if statuses.count("HIGH") >= 2:
        return "TOO WET"

    return "OK"

def daily_average_moisture(slot_statuses):
    values = [
        s["value"]
        for s in slot_statuses.values()
        if s["value"] is not None
    ]

    if not values:
        return None

    return round(sum(values) / len(values))

