from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .database import DEFAULT_DB_PATH, connect


NATION_NAME_SQL = """
CASE n.name
    WHEN 'USA' THEN '미국'
    WHEN 'Germany' THEN '독일'
    WHEN 'USSR' THEN '소련'
    WHEN 'Britain' THEN '영국'
    WHEN 'Japan' THEN '일본'
    WHEN 'China' THEN '중국'
    WHEN 'Italy' THEN '이탈리아'
    WHEN 'France' THEN '프랑스'
    WHEN 'Sweden' THEN '스웨덴'
    WHEN 'Israel' THEN '이스라엘'
    ELSE n.name
END
"""

VEHICLE_TYPE_NAME_SQL = """
CASE vt.name
    WHEN 'Light Tank' THEN '경전차'
    WHEN 'Medium Tank' THEN '중형전차'
    WHEN 'Heavy Tank' THEN '중전차'
    WHEN 'Tank Destroyer' THEN '구축전차'
    WHEN 'SPAA' THEN '자주대공포'
    ELSE vt.name
END
"""


class BaseRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    def _next_id(self, conn: Any, table: str, column: str) -> int:
        value = conn.execute(f"SELECT COALESCE(MAX({column}), 0) + 1 FROM {table}").fetchone()[0]
        return int(value)


class NationRepository(BaseRepository):
    def find_all(self) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    n.nation_id,
                    {NATION_NAME_SQL} AS name,
                    n.flag_image_path
                FROM nation n
                ORDER BY name
                """
            ).fetchdf()


class VehicleTypeRepository(BaseRepository):
    def find_all(self) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    vt.type_id,
                    {VEHICLE_TYPE_NAME_SQL} AS name,
                    vt.description
                FROM vehicle_type vt
                ORDER BY vt.type_id
                """
            ).fetchdf()


class VehicleRepository(BaseRepository):
    def save(self, data: dict[str, Any]) -> int:
        with connect(self.db_path) as conn:
            vehicle_id = self._next_id(conn, "vehicle", "vehicle_id")
            conn.execute(
                """
                INSERT INTO vehicle
                (vehicle_id, nation_id, type_id, name, vehicle_rank, battle_rating, repair_cost, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    vehicle_id,
                    data["nation_id"],
                    data["type_id"],
                    data["name"],
                    data["vehicle_rank"],
                    data["battle_rating"],
                    data["repair_cost"],
                    data.get("image_path", ""),
                ],
            )
            return vehicle_id

    def find_by_id(self, vehicle_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    v.*,
                    {NATION_NAME_SQL} AS nation_name,
                    {VEHICLE_TYPE_NAME_SQL} AS type_name,
                    ts.front_armor_mm,
                    ts.side_armor_mm,
                    ts.rear_armor_mm,
                    s.name AS representative_shell_name,
                    s.shell_type,
                    s.penetration_500m_0deg
                FROM vehicle v
                JOIN nation n ON v.nation_id = n.nation_id
                JOIN vehicle_type vt ON v.type_id = vt.type_id
                LEFT JOIN tank_spec ts ON v.vehicle_id = ts.vehicle_id
                LEFT JOIN shell s ON v.vehicle_id = s.vehicle_id AND s.is_representative = TRUE
                WHERE v.vehicle_id = ?
                """,
                [vehicle_id],
            ).fetchdf()

    def find_by_filter(
        self,
        nation_id: int | None = None,
        type_id: int | None = None,
        br_min: float | None = None,
        br_max: float | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        clauses: list[str] = []
        params: list[Any] = []
        if nation_id:
            clauses.append("v.nation_id = ?")
            params.append(nation_id)
        if type_id:
            clauses.append("v.type_id = ?")
            params.append(type_id)
        if br_min is not None:
            clauses.append("v.battle_rating >= ?")
            params.append(br_min)
        if br_max is not None:
            clauses.append("v.battle_rating <= ?")
            params.append(br_max)
        if keyword:
            clauses.append("LOWER(v.name) LIKE ?")
            params.append(f"%{keyword.lower()}%")

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    v.vehicle_id,
                    v.name,
                    {NATION_NAME_SQL} AS nation,
                    {VEHICLE_TYPE_NAME_SQL} AS vehicle_type,
                    v.vehicle_rank,
                    v.battle_rating,
                    v.repair_cost,
                    v.image_path
                FROM vehicle v
                JOIN nation n ON v.nation_id = n.nation_id
                JOIN vehicle_type vt ON v.type_id = vt.type_id
                {where_sql}
                ORDER BY nation, v.battle_rating, v.name
                """,
                params,
            ).fetchdf()

    def exists_by_nation_and_name(self, nation_id: int, name: str) -> bool:
        with connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM vehicle WHERE nation_id = ? AND LOWER(name) = ?",
                [nation_id, name.lower()],
            ).fetchone()[0]
            return bool(count)

    def delete_by_id(self, vehicle_id: int) -> bool:
        with connect(self.db_path) as conn:
            conn.execute("DELETE FROM shell WHERE vehicle_id = ?", [vehicle_id])
            conn.execute("DELETE FROM tank_spec WHERE vehicle_id = ?", [vehicle_id])
            conn.execute("DELETE FROM vehicle WHERE vehicle_id = ?", [vehicle_id])
            return True


class TankSpecRepository(BaseRepository):
    def save(self, vehicle_id: int, front: int, side: int, rear: int) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tank_spec VALUES (?, ?, ?, ?)",
                [vehicle_id, front, side, rear],
            )


class ShellRepository(BaseRepository):
    def save(self, data: dict[str, Any]) -> int:
        with connect(self.db_path) as conn:
            shell_id = self._next_id(conn, "shell", "shell_id")
            conn.execute(
                f"""
                INSERT INTO shell
                (shell_id, vehicle_id, name, shell_type, penetration_500m_0deg, is_representative)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    shell_id,
                    data["vehicle_id"],
                    data["name"],
                    data.get("shell_type", ""),
                    data["penetration_500m_0deg"],
                    data.get("is_representative", True),
                ],
            )
            return shell_id

    def find_by_vehicle_id(self, vehicle_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                "SELECT * FROM shell WHERE vehicle_id = ? ORDER BY is_representative DESC, name",
                [vehicle_id],
            ).fetchdf()


class LineupRepository(BaseRepository):
    def save(self, data: dict[str, Any]) -> int:
        with connect(self.db_path) as conn:
            lineup_id = self._next_id(conn, "lineup", "lineup_id")
            conn.execute(
                f"""
                INSERT INTO lineup
                (lineup_id, nation_id, title, game_mode, target_br, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [
                    lineup_id,
                    data["nation_id"],
                    data["title"],
                    data["game_mode"],
                    data["target_br"],
                ],
            )
            return lineup_id

    def find_all(self) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT l.*, {NATION_NAME_SQL} AS nation_name
                FROM lineup l
                JOIN nation n ON l.nation_id = n.nation_id
                ORDER BY l.created_at DESC
                """
            ).fetchdf()

    def find_by_nation_id(self, nation_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT l.*, {NATION_NAME_SQL} AS nation_name
                FROM lineup l
                JOIN nation n ON l.nation_id = n.nation_id
                WHERE l.nation_id = ?
                ORDER BY l.created_at DESC
                """,
                [nation_id],
            ).fetchdf()

    def find_by_id(self, lineup_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT l.*, {NATION_NAME_SQL} AS nation_name
                FROM lineup l
                JOIN nation n ON l.nation_id = n.nation_id
                WHERE l.lineup_id = ?
                """,
                [lineup_id],
            ).fetchdf()


class LineupVehicleRepository(BaseRepository):
    def save(self, lineup_id: int, vehicle_id: int, slot_no: int, role_note: str = "") -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO lineup_vehicle VALUES (?, ?, ?, ?)",
                [lineup_id, vehicle_id, slot_no, role_note],
            )

    def find_by_lineup_id(self, lineup_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                "SELECT * FROM lineup_vehicle WHERE lineup_id = ? ORDER BY slot_no",
                [lineup_id],
            ).fetchdf()

    def exists_by_vehicle_id(self, vehicle_id: int) -> bool:
        with connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM lineup_vehicle WHERE vehicle_id = ?",
                [vehicle_id],
            ).fetchone()[0]
            return bool(count)

    def exists_by_slot_no(self, lineup_id: int, slot_no: int) -> bool:
        with connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM lineup_vehicle WHERE lineup_id = ? AND slot_no = ?",
                [lineup_id, slot_no],
            ).fetchone()[0]
            return bool(count)

    def exists_by_lineup_and_vehicle(self, lineup_id: int, vehicle_id: int) -> bool:
        with connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM lineup_vehicle WHERE lineup_id = ? AND vehicle_id = ?",
                [lineup_id, vehicle_id],
            ).fetchone()[0]
            return bool(count)

    def find_vehicle_id_by_slot(self, lineup_id: int, slot_no: int) -> int | None:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT vehicle_id FROM lineup_vehicle WHERE lineup_id = ? AND slot_no = ?",
                [lineup_id, slot_no],
            ).fetchone()
            return int(row[0]) if row else None

    def delete_by_lineup_and_slot(self, lineup_id: int, slot_no: int) -> bool:
        with connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM lineup_vehicle WHERE lineup_id = ? AND slot_no = ?",
                [lineup_id, slot_no],
            )
            return True

    def delete_by_lineup_and_vehicle(self, lineup_id: int, vehicle_id: int) -> bool:
        with connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM lineup_vehicle WHERE lineup_id = ? AND vehicle_id = ?",
                [lineup_id, vehicle_id],
            )
            return True


class LineupQueryRepository(BaseRepository):
    def find_lineup_detail(self, lineup_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    l.lineup_id,
                    l.title AS lineup_title,
                    {NATION_NAME_SQL} AS lineup_nation,
                    l.game_mode,
                    lv.slot_no,
                    v.vehicle_id,
                    v.name AS vehicle_name,
                    {VEHICLE_TYPE_NAME_SQL} AS vehicle_type,
                    v.vehicle_rank,
                    v.battle_rating,
                    v.repair_cost,
                    lv.role_note
                FROM lineup l
                JOIN nation n ON l.nation_id = n.nation_id
                JOIN lineup_vehicle lv ON l.lineup_id = lv.lineup_id
                JOIN vehicle v ON lv.vehicle_id = v.vehicle_id
                JOIN vehicle_type vt ON v.type_id = vt.type_id
                WHERE l.lineup_id = ?
                  AND v.nation_id = l.nation_id
                ORDER BY lv.slot_no
                """,
                [lineup_id],
            ).fetchdf()

    def analyze_lineup(self, lineup_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT
                    l.lineup_id,
                    l.title AS lineup_title,
                    {NATION_NAME_SQL} AS lineup_nation,
                    COUNT(v.vehicle_id) AS vehicle_count,
                    ROUND(AVG(v.battle_rating), 1) AS average_br,
                    MAX(v.battle_rating) AS lineup_battle_rating,
                    SUM(v.repair_cost) AS total_repair_cost
                FROM lineup l
                JOIN nation n ON l.nation_id = n.nation_id
                LEFT JOIN lineup_vehicle lv ON l.lineup_id = lv.lineup_id
                LEFT JOIN vehicle v ON lv.vehicle_id = v.vehicle_id AND v.nation_id = l.nation_id
                WHERE l.lineup_id = ?
                GROUP BY l.lineup_id, l.title, lineup_nation
                """,
                [lineup_id],
            ).fetchdf()

    def analyze_lineup_type_count(self, lineup_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                f"""
                SELECT {VEHICLE_TYPE_NAME_SQL} AS vehicle_type, COUNT(*) AS type_count
                FROM lineup l
                JOIN lineup_vehicle lv ON l.lineup_id = lv.lineup_id
                JOIN vehicle v ON lv.vehicle_id = v.vehicle_id
                JOIN vehicle_type vt ON v.type_id = vt.type_id
                WHERE l.lineup_id = ?
                  AND v.nation_id = l.nation_id
                GROUP BY vehicle_type
                ORDER BY type_count DESC
                """,
                [lineup_id],
            ).fetchdf()

    def analyze_vehicle_against_match_br(self, lineup_id: int, vehicle_id: int) -> pd.DataFrame:
        with connect(self.db_path) as conn:
            return conn.execute(
                """
                WITH lineup_br AS (
                    SELECT MAX(v.battle_rating) AS max_br
                    FROM lineup_vehicle lv
                    JOIN vehicle v ON lv.vehicle_id = v.vehicle_id
                    WHERE lv.lineup_id = ?
                ),
                representative_shell AS (
                    SELECT vehicle_id, name AS shell_name, shell_type, penetration_500m_0deg
                    FROM shell
                    WHERE is_representative = TRUE
                ),
                comparison_avg AS (
                    SELECT
                        COUNT(*) AS comparison_count,
                        AVG(rs.penetration_500m_0deg) AS avg_penetration,
                        AVG(ts.front_armor_mm) AS avg_front_armor,
                        AVG(ts.side_armor_mm) AS avg_side_armor,
                        AVG(ts.rear_armor_mm) AS avg_rear_armor
                    FROM vehicle v
                    JOIN tank_spec ts ON v.vehicle_id = ts.vehicle_id
                    JOIN representative_shell rs ON v.vehicle_id = rs.vehicle_id
                    JOIN lineup_br lb ON v.battle_rating BETWEEN lb.max_br - 1.0 AND lb.max_br + 1.0
                )
                SELECT
                    lb.max_br AS lineup_battle_rating,
                    lb.max_br - 1.0 AS comparison_br_min,
                    lb.max_br + 1.0 AS comparison_br_max,
                    v.vehicle_id,
                    v.name AS vehicle_name,
                    v.battle_rating,
                    rs.shell_name,
                    rs.shell_type,
                    rs.penetration_500m_0deg,
                    ts.front_armor_mm,
                    ts.side_armor_mm,
                    ts.rear_armor_mm,
                    ca.comparison_count,
                    ca.avg_penetration,
                    ca.avg_front_armor,
                    ca.avg_side_armor,
                    ca.avg_rear_armor
                FROM vehicle v
                JOIN tank_spec ts ON v.vehicle_id = ts.vehicle_id
                JOIN representative_shell rs ON v.vehicle_id = rs.vehicle_id
                CROSS JOIN lineup_br lb
                CROSS JOIN comparison_avg ca
                WHERE v.vehicle_id = ?
                """,
                [lineup_id, vehicle_id],
            ).fetchdf()
