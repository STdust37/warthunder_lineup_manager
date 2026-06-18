from __future__ import annotations

from pathlib import Path

import duckdb

from . import data_source
from .interfaces import SeedDataProviderInterface


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "war_thunder.duckdb"


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path))


def init_database(
    db_path: str | Path = DEFAULT_DB_PATH,
    seed: bool = True,
    seed_provider: SeedDataProviderInterface | None = None,
) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    provider = seed_provider or data_source.StaticSeedDataProvider()
    with connect(db_path) as conn:
        create_schema(conn)
        if seed:
            seed_database(conn, provider)
            sync_reference_data(conn, provider)
        ensure_default_vehicle_images(conn)


def create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nation (
            nation_id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            flag_image_path VARCHAR
        );

        CREATE TABLE IF NOT EXISTS vehicle_type (
            type_id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            description VARCHAR
        );

        CREATE TABLE IF NOT EXISTS vehicle (
            vehicle_id INTEGER PRIMARY KEY,
            nation_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            vehicle_rank INTEGER NOT NULL CHECK (vehicle_rank BETWEEN 1 AND 8),
            battle_rating DOUBLE NOT NULL CHECK (battle_rating >= 1.0),
            repair_cost INTEGER NOT NULL DEFAULT 0 CHECK (repair_cost >= 0),
            image_path VARCHAR,
            UNIQUE (nation_id, name),
            FOREIGN KEY (nation_id) REFERENCES nation(nation_id),
            FOREIGN KEY (type_id) REFERENCES vehicle_type(type_id)
        );

        CREATE TABLE IF NOT EXISTS tank_spec (
            vehicle_id INTEGER PRIMARY KEY,
            front_armor_mm INTEGER NOT NULL CHECK (front_armor_mm >= 0),
            side_armor_mm INTEGER NOT NULL CHECK (side_armor_mm >= 0),
            rear_armor_mm INTEGER NOT NULL CHECK (rear_armor_mm >= 0),
            FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
        );

        CREATE TABLE IF NOT EXISTS shell (
            shell_id INTEGER PRIMARY KEY,
            vehicle_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            shell_type VARCHAR,
            penetration_500m_0deg INTEGER NOT NULL CHECK (penetration_500m_0deg >= 0),
            is_representative BOOLEAN NOT NULL DEFAULT FALSE,
            FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
        );

        CREATE TABLE IF NOT EXISTS lineup (
            lineup_id INTEGER PRIMARY KEY,
            nation_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            game_mode VARCHAR NOT NULL CHECK (game_mode IN ('Arcade', 'Realistic', 'Simulator')),
            target_br DOUBLE NOT NULL CHECK (target_br >= 1.0),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nation_id) REFERENCES nation(nation_id)
        );

        CREATE TABLE IF NOT EXISTS lineup_vehicle (
            lineup_id INTEGER NOT NULL,
            vehicle_id INTEGER NOT NULL,
            slot_no INTEGER NOT NULL CHECK (slot_no BETWEEN 1 AND 10),
            role_note VARCHAR,
            PRIMARY KEY (lineup_id, slot_no),
            UNIQUE (lineup_id, vehicle_id),
            FOREIGN KEY (lineup_id) REFERENCES lineup(lineup_id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
        );
        """
    )


def seed_database(
    conn: duckdb.DuckDBPyConnection,
    provider: SeedDataProviderInterface | None = None,
) -> None:
    if conn.execute("SELECT COUNT(*) FROM nation").fetchone()[0] > 0:
        return
    provider = provider or data_source.StaticSeedDataProvider()

    conn.executemany(
        "INSERT INTO nation VALUES (?, ?, ?)",
        provider.fetch_nations(),
    )
    conn.executemany(
        "INSERT INTO vehicle_type VALUES (?, ?, ?)",
        provider.fetch_vehicle_types(),
    )

    vehicles = provider.fetch_vehicle_seed_rows()

    conn.executemany(
        """
        INSERT INTO vehicle
        (vehicle_id, nation_id, type_id, name, vehicle_rank, battle_rating, repair_cost, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [row[:8] for row in vehicles],
    )
    conn.executemany(
        "INSERT INTO tank_spec VALUES (?, ?, ?, ?)",
        [(row[0], row[8], row[9], row[10]) for row in vehicles],
    )
    conn.executemany(
        """
        INSERT INTO shell
        (shell_id, vehicle_id, name, shell_type, penetration_500m_0deg, is_representative)
        VALUES (?, ?, ?, ?, ?, TRUE)
        """,
        [(idx + 1, row[0], row[11], row[12], row[13]) for idx, row in enumerate(vehicles)],
    )

    conn.executemany(
        """
        INSERT INTO lineup
        (lineup_id, nation_id, title, game_mode, target_br, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        provider.fetch_lineups(),
    )
    conn.executemany(
        "INSERT INTO lineup_vehicle VALUES (?, ?, ?, ?)",
        provider.fetch_lineup_vehicles(),
    )


def sync_reference_data(
    conn: duckdb.DuckDBPyConnection,
    provider: SeedDataProviderInterface,
) -> None:
    for nation_id, name, flag_image_path in provider.fetch_nations():
        exists = conn.execute(
            "SELECT COUNT(*) FROM nation WHERE nation_id = ?",
            [nation_id],
        ).fetchone()[0]
        if not exists:
            conn.execute(
                "INSERT INTO nation VALUES (?, ?, ?)",
                [nation_id, name, flag_image_path],
            )

    for type_id, name, description in provider.fetch_vehicle_types():
        exists = conn.execute(
            "SELECT COUNT(*) FROM vehicle_type WHERE type_id = ?",
            [type_id],
        ).fetchone()[0]
        if not exists:
            conn.execute(
                "INSERT INTO vehicle_type VALUES (?, ?, ?)",
                [type_id, name, description],
            )

    for row in provider.fetch_vehicle_seed_rows():
        preferred_vehicle_id = int(row[0])
        nation_id = int(row[1])
        name = str(row[3])
        existing = conn.execute(
            "SELECT vehicle_id FROM vehicle WHERE nation_id = ? AND name = ?",
            [nation_id, name],
        ).fetchone()
        if existing:
            vehicle_id = int(existing[0])
            conn.execute(
                """
                UPDATE vehicle
                SET image_path = ?
                WHERE vehicle_id = ?
                  AND (image_path IS NULL OR TRIM(image_path) = '' OR image_path = ?)
                """,
                [row[7], vehicle_id, data_source.DEFAULT_VEHICLE_IMAGE_PATH],
            )
        else:
            id_available = conn.execute(
                "SELECT COUNT(*) FROM vehicle WHERE vehicle_id = ?",
                [preferred_vehicle_id],
            ).fetchone()[0] == 0
            vehicle_id = preferred_vehicle_id if id_available else _next_id(conn, "vehicle", "vehicle_id")
            conn.execute(
                """
                INSERT INTO vehicle
                (vehicle_id, nation_id, type_id, name, vehicle_rank, battle_rating, repair_cost, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [vehicle_id, *row[1:8]],
            )

        spec_exists = conn.execute(
            "SELECT COUNT(*) FROM tank_spec WHERE vehicle_id = ?",
            [vehicle_id],
        ).fetchone()[0]
        if not spec_exists:
            conn.execute(
                "INSERT INTO tank_spec VALUES (?, ?, ?, ?)",
                [vehicle_id, row[8], row[9], row[10]],
            )

        shell_exists = conn.execute(
            "SELECT COUNT(*) FROM shell WHERE vehicle_id = ? AND is_representative = TRUE",
            [vehicle_id],
        ).fetchone()[0]
        if not shell_exists:
            conn.execute(
                """
                INSERT INTO shell
                (shell_id, vehicle_id, name, shell_type, penetration_500m_0deg, is_representative)
                VALUES (?, ?, ?, ?, ?, TRUE)
                """,
                [_next_id(conn, "shell", "shell_id"), vehicle_id, row[11], row[12], row[13]],
            )


def _next_id(conn: duckdb.DuckDBPyConnection, table: str, column: str) -> int:
    value = conn.execute(f"SELECT COALESCE(MAX({column}), 0) + 1 FROM {table}").fetchone()[0]
    return int(value)


def ensure_default_vehicle_images(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        UPDATE vehicle
        SET image_path = ?
        WHERE image_path IS NULL OR TRIM(image_path) = ''
        """,
        [data_source.DEFAULT_VEHICLE_IMAGE_PATH],
    )
    for name, image_path in data_source.VEHICLE_IMAGE_PATHS.items():
        conn.execute(
            """
            UPDATE vehicle
            SET image_path = ?
            WHERE name = ?
              AND (image_path IS NULL OR TRIM(image_path) = '' OR image_path = ?)
            """,
            [image_path, name, data_source.DEFAULT_VEHICLE_IMAGE_PATH],
        )
