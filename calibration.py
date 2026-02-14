# calibration.py

WET_REF_RAW = 2323     # wet soil after 5–10 min drain (your pot test)
DRY_REF_RAW = 3500     # dry soil in your pot mix
OUT_OF_SOIL_RAW = 3600 # air/unplugged range

def raw_to_pct(raw: int, wet: int = WET_REF_RAW, dry: int = DRY_REF_RAW) -> int:
    if raw is None:
        return 0
    if raw >= OUT_OF_SOIL_RAW:
        return 0

    # clamp
    raw = max(wet, min(dry, raw))

    pct = int(round((dry - raw) * 100.0 / (dry - wet)))
    return max(0, min(100, pct))

