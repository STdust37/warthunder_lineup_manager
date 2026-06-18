from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .database import DEFAULT_DB_PATH, init_database
from .interfaces import (
    LineupQueryRepositoryInterface,
    LineupRepositoryInterface,
    LineupVehicleRepositoryInterface,
    NationRepositoryInterface,
    ShellRepositoryInterface,
    TankSpecRepositoryInterface,
    VehicleRepositoryInterface,
    VehicleTypeRepositoryInterface,
)
from .repositories import (
    LineupQueryRepository,
    LineupRepository,
    LineupVehicleRepository,
    NationRepository,
    ShellRepository,
    TankSpecRepository,
    VehicleRepository,
    VehicleTypeRepository,
)


class AppService:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        init_database(self.db_path)
        self.nations: NationRepositoryInterface = NationRepository(self.db_path)
        self.vehicle_types: VehicleTypeRepositoryInterface = VehicleTypeRepository(self.db_path)
        self.vehicles: VehicleRepositoryInterface = VehicleRepository(self.db_path)
        self.tank_specs: TankSpecRepositoryInterface = TankSpecRepository(self.db_path)
        self.shells: ShellRepositoryInterface = ShellRepository(self.db_path)
        self.lineups: LineupRepositoryInterface = LineupRepository(self.db_path)
        self.lineup_vehicles: LineupVehicleRepositoryInterface = LineupVehicleRepository(self.db_path)
        self.lineup_queries: LineupQueryRepositoryInterface = LineupQueryRepository(self.db_path)

    def list_nations(self) -> pd.DataFrame:
        return self.nations.find_all()

    def list_vehicle_types(self) -> pd.DataFrame:
        return self.vehicle_types.find_all()

    def search_vehicles(
        self,
        nation_id: int | None = None,
        type_id: int | None = None,
        br_min: float | None = None,
        br_max: float | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        return self.vehicles.find_by_filter(nation_id, type_id, br_min, br_max, keyword)

    def create_vehicle(
        self,
        vehicle_data: dict[str, Any],
        armor_data: dict[str, int],
        shell_data: dict[str, Any],
    ) -> int:
        if self.vehicles.exists_by_nation_and_name(vehicle_data["nation_id"], vehicle_data["name"]):
            raise ValueError("같은 국가에 동일한 장비명이 이미 존재합니다.")
        vehicle_id = self.vehicles.save(vehicle_data)
        self.tank_specs.save(
            vehicle_id,
            armor_data["front_armor_mm"],
            armor_data["side_armor_mm"],
            armor_data["rear_armor_mm"],
        )
        self.shells.save(
            {
                "vehicle_id": vehicle_id,
                "name": shell_data["name"],
                "shell_type": shell_data.get("shell_type", ""),
                "penetration_500m_0deg": shell_data["penetration_500m_0deg"],
                "is_representative": True,
            }
        )
        return vehicle_id

    def delete_vehicle(self, vehicle_id: int) -> bool:
        if self.lineup_vehicles.exists_by_vehicle_id(vehicle_id):
            raise ValueError("라인업에 포함된 장비는 먼저 라인업에서 제거해야 삭제할 수 있습니다.")
        return self.vehicles.delete_by_id(vehicle_id)

    def list_lineups(self, nation_id: int | None = None) -> pd.DataFrame:
        if nation_id:
            return self.lineups.find_by_nation_id(nation_id)
        return self.lineups.find_all()

    def create_lineup(
        self,
        nation_id: int,
        title: str,
        game_mode: str,
        target_br: float,
    ) -> int:
        if not title.strip():
            raise ValueError("라인업 이름을 입력해야 합니다.")
        return self.lineups.save(
            {
                "nation_id": nation_id,
                "title": title.strip(),
                "game_mode": game_mode,
                "target_br": target_br,
            }
        )

    def add_vehicle_to_lineup(
        self,
        lineup_id: int,
        vehicle_id: int,
        slot_no: int,
    ) -> None:
        lineup_df = self.lineups.find_by_id(lineup_id)
        vehicle_df = self.vehicles.find_by_id(vehicle_id)
        if lineup_df.empty:
            raise ValueError("선택한 라인업을 찾을 수 없습니다.")
        if vehicle_df.empty:
            raise ValueError("선택한 장비를 찾을 수 없습니다.")
        lineup_nation_id = int(lineup_df.iloc[0]["nation_id"])
        vehicle_nation_id = int(vehicle_df.iloc[0]["nation_id"])
        if lineup_nation_id != vehicle_nation_id:
            raise ValueError("라인업 국가와 같은 국가의 장비만 추가할 수 있습니다.")

        if slot_no < 1 or slot_no > 10:
            raise ValueError("슬롯 번호는 1번부터 10번까지 선택할 수 있습니다.")

        existing_vehicle_id = self.lineup_vehicles.find_vehicle_id_by_slot(lineup_id, slot_no)
        if existing_vehicle_id != vehicle_id and self.lineup_vehicles.exists_by_lineup_and_vehicle(lineup_id, vehicle_id):
            raise ValueError("선택한 장비는 이미 이 라인업의 다른 슬롯에 배치되어 있습니다.")
        if existing_vehicle_id is not None:
            self.lineup_vehicles.delete_by_lineup_and_slot(lineup_id, slot_no)
        self.lineup_vehicles.save(lineup_id, vehicle_id, slot_no, "")

    def remove_vehicle_from_lineup(self, lineup_id: int, vehicle_id: int) -> bool:
        return self.lineup_vehicles.delete_by_lineup_and_vehicle(lineup_id, vehicle_id)

    def lineup_detail(self, lineup_id: int) -> pd.DataFrame:
        return self.lineup_queries.find_lineup_detail(lineup_id)

    def lineup_analysis(self, lineup_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        return (
            self.lineup_queries.analyze_lineup(lineup_id),
            self.lineup_queries.analyze_lineup_type_count(lineup_id),
        )

    def vehicle_match_analysis(self, lineup_id: int, vehicle_id: int) -> pd.DataFrame:
        raw = self.lineup_queries.analyze_vehicle_against_match_br(lineup_id, vehicle_id)
        if raw.empty:
            return raw

        row = raw.iloc[0].to_dict()
        metrics = [
            ("관통력", "penetration_500m_0deg", "avg_penetration", "mm"),
            ("정면 장갑", "front_armor_mm", "avg_front_armor", "mm"),
            ("측면 장갑", "side_armor_mm", "avg_side_armor", "mm"),
            ("후면 장갑", "rear_armor_mm", "avg_rear_armor", "mm"),
        ]
        result_rows: list[dict[str, Any]] = []
        for label, selected_key, average_key, unit in metrics:
            selected = float(row[selected_key])
            average = float(row[average_key] or 0)
            diff_pct = 0.0 if average == 0 else ((selected - average) / average) * 100
            status = self._status_from_diff(diff_pct)
            result_rows.append(
                {
                    "항목": label,
                    "선택 전차": round(selected, 1),
                    "비교군 평균": round(average, 1),
                    "차이(%)": round(diff_pct, 1),
                    "판정": status,
                    "단위": unit,
                    "lineup_battle_rating": row["lineup_battle_rating"],
                    "comparison_br_min": row["comparison_br_min"],
                    "comparison_br_max": row["comparison_br_max"],
                    "comparison_count": row["comparison_count"],
                    "vehicle_name": row["vehicle_name"],
                    "vehicle_br": row["battle_rating"],
                    "shell_name": row["shell_name"],
                    "shell_type": row["shell_type"],
                }
            )
        return pd.DataFrame(result_rows)

    def summary(self) -> dict[str, Any]:
        vehicles = self.search_vehicles()
        lineups = self.list_lineups()
        nations = self.list_nations()
        return {
            "vehicle_count": len(vehicles),
            "lineup_count": len(lineups),
            "nation_count": len(nations),
            "recent_lineup": lineups.iloc[0]["title"] if not lineups.empty else "-",
        }

    @staticmethod
    def _status_from_diff(diff_pct: float) -> str:
        if diff_pct >= 35:
            return "매우 높음"
        if diff_pct >= 15:
            return "높음"
        if diff_pct >= 5:
            return "약간 높음"
        if diff_pct <= -35:
            return "매우 낮음"
        if diff_pct <= -15:
            return "낮음"
        if diff_pct <= -5:
            return "약간 낮음"
        return "비슷함"
