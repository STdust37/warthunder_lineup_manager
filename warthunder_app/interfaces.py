from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import pandas as pd


class SeedDataProviderInterface(Protocol):
    """초기 데이터 공급 인터페이스"""

    def fetch_nations(self) -> list[tuple[int, str, str]]: ...

    def fetch_vehicle_types(self) -> list[tuple[int, str, str]]: ...

    def fetch_vehicle_seed_rows(self) -> list[tuple[Any, ...]]: ...

    def fetch_lineups(self) -> list[tuple[int, int, str, str, float]]: ...

    def fetch_lineup_vehicles(self) -> list[tuple[int, int, int, str]]: ...


class NationRepositoryInterface(Protocol):
    """국가 목록 조회 인터페이스"""

    db_path: Path

    def find_all(self) -> pd.DataFrame: ...


class VehicleTypeRepositoryInterface(Protocol):
    """전차 병과 목록 조회 인터페이스"""

    db_path: Path

    def find_all(self) -> pd.DataFrame: ...


class VehicleRepositoryInterface(Protocol):
    """장비 등록, 조회, 삭제 인터페이스"""

    db_path: Path

    def save(self, data: dict[str, Any]) -> int: ...

    def find_by_id(self, vehicle_id: int) -> pd.DataFrame: ...

    def find_by_filter(
        self,
        nation_id: int | None = None,
        type_id: int | None = None,
        br_min: float | None = None,
        br_max: float | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame: ...

    def exists_by_nation_and_name(self, nation_id: int, name: str) -> bool: ...

    def delete_by_id(self, vehicle_id: int) -> bool: ...


class TankSpecRepositoryInterface(Protocol):
    """전차 장갑 제원 저장 인터페이스"""

    db_path: Path

    def save(self, vehicle_id: int, front: int, side: int, rear: int) -> None: ...


class ShellRepositoryInterface(Protocol):
    """대표 포탄 관통력 저장 및 조회 인터페이스"""

    db_path: Path

    def save(self, data: dict[str, Any]) -> int: ...

    def find_by_vehicle_id(self, vehicle_id: int) -> pd.DataFrame: ...


class LineupRepositoryInterface(Protocol):
    """국가별 라인업 생성 및 목록 조회 인터페이스"""

    db_path: Path

    def save(self, data: dict[str, Any]) -> int: ...

    def find_all(self) -> pd.DataFrame: ...

    def find_by_nation_id(self, nation_id: int) -> pd.DataFrame: ...

    def find_by_id(self, lineup_id: int) -> pd.DataFrame: ...


class LineupVehicleRepositoryInterface(Protocol):
    """라인업 슬롯 장비 배치, 교체, 삭제 인터페이스"""

    db_path: Path

    def save(self, lineup_id: int, vehicle_id: int, slot_no: int, role_note: str = "") -> None: ...

    def find_by_lineup_id(self, lineup_id: int) -> pd.DataFrame: ...

    def exists_by_vehicle_id(self, vehicle_id: int) -> bool: ...

    def exists_by_slot_no(self, lineup_id: int, slot_no: int) -> bool: ...

    def exists_by_lineup_and_vehicle(self, lineup_id: int, vehicle_id: int) -> bool: ...

    def find_vehicle_id_by_slot(self, lineup_id: int, slot_no: int) -> int | None: ...

    def delete_by_lineup_and_slot(self, lineup_id: int, slot_no: int) -> bool: ...

    def delete_by_lineup_and_vehicle(self, lineup_id: int, vehicle_id: int) -> bool: ...


class LineupQueryRepositoryInterface(Protocol):
    """라인업 상세 조회 및 분석용 Join 조회 인터페이스"""

    db_path: Path

    def find_lineup_detail(self, lineup_id: int) -> pd.DataFrame: ...

    def analyze_lineup(self, lineup_id: int) -> pd.DataFrame: ...

    def analyze_lineup_type_count(self, lineup_id: int) -> pd.DataFrame: ...

    def analyze_vehicle_against_match_br(self, lineup_id: int, vehicle_id: int) -> pd.DataFrame: ...
