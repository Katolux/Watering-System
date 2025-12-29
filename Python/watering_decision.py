from dataclasses import dataclass

@dataclass
class WateringInputs:
    avg_temp: float
    soil_moisture: int
    rain_last_24h: float
    # rain_today: float


def temperature_rule(temp_c):
    if temp_c < 15:
        return -10
    elif temp_c < 20:
        return 0
    elif temp_c < 25:
        return +5
    elif temp_c < 30:
        return +10
    else:
        return +15


def soil_moisture_rule(moisture):
    if moisture > 2500:
        return -20
    elif moisture > 1800:
        return -10
    elif moisture > 1200:
        return 0
    else:
        return +10


def rain_rule(rain_mm):
    if rain_mm > 10:
        return -20
    elif rain_mm > 3:
        return -10
    else:
        return 0


class WateringDecision:
    def __init__(self, base_minutes=45):
        self.base_minutes = base_minutes

    def calculate(self, inputs):
        total = self.base_minutes
        breakdown = {}

        breakdown["temperature"] = temperature_rule(inputs.avg_temp)
        breakdown["soil"] = soil_moisture_rule(inputs.soil_moisture)
        breakdown["rain"] = rain_rule(inputs.rain_last_24h)

        for delta in breakdown.values():
            total += delta

        return max(total, 0), breakdown


if __name__ == "__main__":
    inputs = WateringInputs(
        avg_temp=30,
        soil_moisture=1250,
        rain_last_24h=0.0
    )

    decision = WateringDecision(base_minutes=45)
    minutes, breakdown = decision.calculate(inputs)

    print("Watering decision")
    print("-----------------")
    print("Base: 45 min")
    for k, v in breakdown.items():
        print(f"{k}: {v:+} min")
    print(f"Final watering time: {minutes} min")
