from gardenhub.db.connection import get_conn


def add_bed(bed_id, active=True, zone_id="default"):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO zones (zone_id, name, active)
            VALUES (?, ?, ?)
            """,
            (zone_id, "Default zone", 1)
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO beds (bed_id, zone_id, active)
            VALUES (?, ?, ?)
            """,
            (bed_id, zone_id, 1 if active else 0)
        )

        conn.commit()


def get_all_beds():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT bed_id, active
            FROM beds
            ORDER BY bed_id
        """)
        rows = cur.fetchall()
    return rows


def assign_plant_to_bed(bed_id, plant_id, variety_id=None, quantity=1, planted_at=None, notes=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bed_plantings
            (bed_id, plant_id, variety_id, quantity, planted_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (bed_id, plant_id, variety_id, quantity, planted_at, notes)
        )
        conn.commit()


def get_beds_with_plants():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                beds.bed_id,
                beds.active,
                GROUP_CONCAT(plants.name, ', ') AS plant_names,
                MIN(plants.min_moisture) AS min_moisture,
                MAX(plants.max_moisture) AS max_moisture,
                MAX(plants.base_minutes) AS base_minutes
            FROM beds
            LEFT JOIN bed_plantings bp
                ON beds.bed_id = bp.bed_id
               AND bp.removed_at IS NULL
            LEFT JOIN plants
                ON bp.plant_id = plants.plant_id
            GROUP BY beds.bed_id, beds.active
            ORDER BY beds.bed_id
            """
        )
        rows = cur.fetchall()
    return rows
