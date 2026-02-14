from dataclasses import dataclass
from typing import Optional


# -----------------------------
# Inputs
# -----------------------------

@dataclass
class WateringInputs:
    base_minutes: int
    avg_moisture: Optional[int]
    min_moisture: int
    max_moisture: int
    temp_max: float
    precipitation: float


# -----------------------------
# Factor functions
# -----------------------------

def soil_factor_from_moisture(avg_moisture, min_m, max_m):
    if avg_moisture is None:
        return 0.8  # conservative when no data
    if avg_moisture < min_m:
        return 1.3
    if avg_moisture > max_m:
        return 0.6
    return 1.0


def temperature_factor(temp_c):
    if temp_c is None:
        return 1.0
    if temp_c < 15:
        return 0.7
    elif temp_c < 20:
        return 0.9
    elif temp_c < 25:
        return 1.0
    elif temp_c < 30:
        return 1.1
    else:
        return 1.25


def rain_factor(precip_mm):
    if precip_mm is None:
        return 1.0
    if precip_mm > 10:
        return 0.0
    elif precip_mm > 5:
        return 0.4
    elif precip_mm > 1:
        return 0.8
    else:
        return 1.0


# -----------------------------
# Decision engine
# -----------------------------

class WateringDecision:
    def calculate(self, inputs: WateringInputs):
        soil_f = soil_factor_from_moisture(
            inputs.avg_moisture,
            inputs.min_moisture,
            inputs.max_moisture
        )

        temp_f = temperature_factor(inputs.temp_max)
        rain_f = rain_factor(inputs.precipitation)

        final_minutes = (
            inputs.base_minutes
            * soil_f
            * temp_f
            * rain_f
        )

        final_minutes = max(0, round(final_minutes))

        breakdown = {
            "soil_factor": soil_f,
            "temp_factor": temp_f,
            "rain_factor": rain_f,
        }

        return final_minutes, breakdown
