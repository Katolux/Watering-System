#Possible ML for end of year for next interation . Just an idea.
#doesnt match current schema


import sqlite3
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

DB_PATH = "garden_system.db"   # single database
MODEL_DIR = Path("ml_models")
MODEL_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# LOADERS
# --------------------------------------------------

def load_weather(conn):
    return pd.read_sql("""
        SELECT
            date,
            temp_max,
            temp_min,
            precipitation,
            sunshine,
            daylight,
            wind_max,
            wind_dir
        FROM weather_daily
    """, conn)


def load_beds(conn):
    return pd.read_sql("""
        SELECT
            bed_id,
            type,
            area_m2,
            volume_l
        FROM beds
    """, conn)


def load_sensor_daily(conn):
    """
    Daily aggregation of sensor readings.
    You can change AVG/MIN/MAX later without touching the schema.
    """
    return pd.read_sql("""
        SELECT
            date(ts) AS date,
            bed_id,
            AVG(moisture_raw) AS moisture_avg,
            MIN(moisture_raw) AS moisture_min,
            MAX(moisture_raw) AS moisture_max
        FROM sensor_readings
        GROUP BY date(ts), bed_id
    """, conn)


def load_watering_daily(conn):
    return pd.read_sql("""
        SELECT
            date(ts) AS date,
            bed_id,
            SUM(duration_s) AS water_seconds
        FROM watering_events
        GROUP BY date(ts), bed_id
    """, conn)


def load_plant_profiles(conn):
    return pd.read_sql("""
        SELECT
            plant_id,
            soil_id,
            moisture_target_min,
            moisture_target_max,
            water_sensitivity
        FROM plant_profiles
    """, conn)


def load_soil_profiles(conn):
    return pd.read_sql("""
        SELECT
            soil_id,
            drainage_score,
            ph_target
        FROM soil_profiles
    """, conn)


def load_plantings(conn):
    return pd.read_sql("""
        SELECT
            bed_id,
            plant_id,
            count
        FROM plantings
    """, conn)

# --------------------------------------------------
# FEATURE ENGINEERING (STATIC BED FEATURES)
# --------------------------------------------------

def build_bed_profile(conn):
    """
    Builds per-bed static features based on plants and soil.
    """
    plantings = load_plantings(conn)
    plants = load_plant_profiles(conn)
    soils = load_soil_profiles(conn)

    df = (
        plantings
        .merge(plants, on="plant_id", how="left")
        .merge(soils, on="soil_id", how="left")
    )

    # Aggregate per bed
    bed_profile = df.groupby("bed_id", as_index=False).agg({
        "count": "sum",
        "moisture_target_min": "mean",
        "moisture_target_max": "mean",
        "water_sensitivity": "mean",
        "drainage_score": "mean",
        "ph_target": "mean",
    })

    bed_profile.rename(columns={"count": "plant_count"}, inplace=True)

    return bed_profile

# --------------------------------------------------
# DATASET BUILDER
# --------------------------------------------------

def build_ml_dataset():
    conn = sqlite3.connect(DB_PATH)

    weather = load_weather(conn)
    beds = load_beds(conn)
    sensor = load_sensor_daily(conn)
    watering = load_watering_daily(conn)
    bed_profile = build_bed_profile(conn)

    conn.close()

    # Base: one row per bed per day (from sensors)
    df = (
        sensor
        .merge(weather, on="date", how="left")
        .merge(watering, on=["date", "bed_id"], how="left")
        .merge(beds, on="bed_id", how="left")
        .merge(bed_profile, on="bed_id", how="left")
    )

    # Labels
    df["water_seconds"] = df["water_seconds"].fillna(0)
    df["watered"] = df["water_seconds"] > 0

    return df

# --------------------------------------------------
# FEATURE / LABEL SPLIT
# --------------------------------------------------

def split_features_labels(df):
    FEATURES = [
        "moisture_avg",
        "moisture_min",
        "moisture_max",
        "temp_max",
        "temp_min",
        "precipitation",
        "sunshine",
        "daylight",
        "wind_max",
        "wind_dir",
        "plant_count",
        "moisture_target_min",
        "moisture_target_max",
        "water_sensitivity",
        "drainage_score",
        "ph_target",
        "area_m2",
        "volume_l",
    ]

    LABEL = "watered"

    X = df[FEATURES]
    y = df[LABEL]

    return X, y

# --------------------------------------------------
# MODEL PLACEHOLDER
# --------------------------------------------------

def train_model(X, y):
    """
    Placeholder only.
    You decide later:
    - rules
    - sklearn
    - hybrid
    """
    print("Training placeholder")
    print("Samples:", len(X))
    return None

# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print("Building ML dataset...")
    df = build_ml_dataset()

    print("Splitting features / labels...")
    X, y = split_features_labels(df)

    print("Training model...")
    model = train_model(X, y)

    print("Done.")

if __name__ == "__main__":
    main()
