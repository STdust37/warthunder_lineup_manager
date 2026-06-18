from __future__ import annotations

from pathlib import Path
from typing import Any

import flet as ft
import pandas as pd

from warthunder_app.database import DEFAULT_DB_PATH
from warthunder_app.services import AppService


APP_TITLE = "War Thunder Lineup Manager"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_VEHICLE_IMAGE = PROJECT_ROOT / "assets" / "vehicle_placeholder.svg"
FLAG_IMAGE_PATHS = {
    "미국": PROJECT_ROOT / "assets" / "flags" / "usa.png",
    "독일": PROJECT_ROOT / "assets" / "flags" / "germany.png",
    "소련": PROJECT_ROOT / "assets" / "flags" / "ussr.png",
    "영국": PROJECT_ROOT / "assets" / "flags" / "britain.png",
    "일본": PROJECT_ROOT / "assets" / "flags" / "japan.png",
    "중국": PROJECT_ROOT / "assets" / "flags" / "china.png",
    "이탈리아": PROJECT_ROOT / "assets" / "flags" / "italy.png",
    "프랑스": PROJECT_ROOT / "assets" / "flags" / "france.png",
    "스웨덴": PROJECT_ROOT / "assets" / "flags" / "sweden.png",
    "이스라엘": PROJECT_ROOT / "assets" / "flags" / "israel.png",
}
NATION_NAME_ALIASES = {
    "USA": "미국",
    "Germany": "독일",
    "USSR": "소련",
    "Britain": "영국",
    "Japan": "일본",
    "China": "중국",
    "Italy": "이탈리아",
    "France": "프랑스",
    "Sweden": "스웨덴",
    "Israel": "이스라엘",
}


class WarThunderApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.service = AppService(DEFAULT_DB_PATH)
        self.nav_index = 0
        self.selected_vehicle_id: int | None = None
        self.lineup_nation_id: int | None = None
        self.selected_lineup_id: int | None = None
        self.selected_lineup_slot_no: int | None = None
        self.selected_lineup_vehicle_id: int | None = None
        self.analysis_nation_id: int | None = None
        self.analysis_lineup_id: int | None = None
        self.analysis_vehicle_id: int | None = None

        self.page.title = APP_TITLE
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#0f1115"
        self.page.padding = 0

    def run(self) -> None:
        self.render()

    def render(self) -> None:
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self._navigation(),
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                    ft.Container(self._screen(), expand=True, padding=24),
                ],
                expand=True,
            )
        )
        self.page.update()

    def _navigation(self) -> ft.NavigationRail:
        destinations = [
            ft.NavigationRailDestination(icon=ft.Icons.HOME, label="홈"),
            ft.NavigationRailDestination(icon=ft.Icons.SEARCH, label="장비 조회"),
            ft.NavigationRailDestination(icon=ft.Icons.ADD_BOX, label="장비 등록"),
            ft.NavigationRailDestination(icon=ft.Icons.VIEW_LIST, label="라인업 관리"),
            ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART, label="분석 조회"),
        ]
        return ft.NavigationRail(
            selected_index=self.nav_index,
            label_type=ft.NavigationRailLabelType.ALL,
            destinations=destinations,
            min_width=116,
            bgcolor=ft.Colors.GREY_900,
            on_change=self._on_nav_change,
        )

    def _screen(self) -> ft.Control:
        screens = [
            self._home_screen,
            self._vehicle_search_screen,
            self._vehicle_form_screen,
            self._lineup_screen,
            self._analysis_screen,
        ]
        return screens[self.nav_index]()

    def _on_nav_change(self, e: ft.ControlEvent) -> None:
        self.nav_index = int(e.control.selected_index)
        self.render()

    def _home_screen(self) -> ft.Control:
        summary = self.service.summary()
        return self._page_column(
            [
                ft.Text(APP_TITLE, size=28, weight=ft.FontWeight.BOLD),
                ft.Text("워썬더 지상전 장비와 국가별 라인업을 관리하는 DuckDB + Flet 애플리케이션"),
                ft.Row(
                    [
                        self._summary_card("등록 장비 수", summary["vehicle_count"]),
                        self._summary_card("저장 라인업 수", summary["lineup_count"]),
                        self._summary_card("국가 수", summary["nation_count"]),
                        self._summary_card("최근 라인업", summary["recent_lineup"]),
                    ],
                    wrap=True,
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("대시보드", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("왼쪽 메뉴에서 장비 조회, 장비 등록, 라인업 관리, 분석 조회 기능을 사용할 수 있습니다."),
                            ft.Text("분석 조회는 매칭 BR 기준 ±1.0 범위의 전차와 선택 전차의 관통력/장갑을 비교합니다."),
                        ],
                        spacing=10,
                    ),
                    border=ft.Border.all(1, ft.Colors.GREY_800),
                    border_radius=8,
                    padding=18,
                    expand=True,
                ),
            ]
        )

    def _vehicle_search_screen(self) -> ft.Control:
        nations = self.service.list_nations()
        types = self.service.list_vehicle_types()

        nation_dd = ft.Dropdown(label="국가", width=180, options=self._nation_options(nations, "전체"))
        type_dd = ft.Dropdown(label="병과", width=180, options=self._options(types, "type_id", "name", "전체"))
        keyword_tf = ft.TextField(label="장비명 검색", width=220)
        br_start_text = ft.Text("1.0", width=44, text_align=ft.TextAlign.CENTER)
        br_end_text = ft.Text("12.0", width=44, text_align=ft.TextAlign.CENTER)
        br_slider = ft.RangeSlider(
            start_value=1.0,
            end_value=12.0,
            label="{value}",
            min=1.0,
            max=12.0,
            divisions=110,
            round=1,
            active_color=ft.Colors.CYAN_700,
            inactive_color=ft.Colors.GREY_700,
            width=260,
        )
        detail_box = ft.Container(border=ft.Border.all(1, ft.Colors.GREY_800), border_radius=8, padding=14, width=360)

        table_box = ft.Container(expand=True)

        def render_detail(vehicle_id: int | None) -> None:
            if not vehicle_id:
                detail_box.content = ft.Text("장비를 선택하면 상세 정보가 표시됩니다.")
                return
            df = self.service.vehicles.find_by_id(vehicle_id)
            if df.empty:
                detail_box.content = ft.Text("장비 정보를 찾을 수 없습니다.")
                return
            row = df.iloc[0]
            detail_box.content = ft.Column(
                [
                    ft.Text(str(row["name"]), size=20, weight=ft.FontWeight.BOLD),
                    self._vehicle_image_card(row.get("image_path"), str(row["name"])),
                    ft.Row([ft.Text("국가:"), self._nation_name_control(row["nation_name"])], spacing=6),
                    ft.Text(f"병과: {row['type_name']}"),
                    ft.Text(f"랭크/BR: {row['vehicle_rank']} / {row['battle_rating']}"),
                    ft.Text(f"수리비: {int(row['repair_cost'])}"),
                    ft.Divider(),
                    ft.Text("대표 성능"),
                    ft.Text(f"대표 포탄: {row['representative_shell_name']} ({row['shell_type']})"),
                    ft.Text(f"관통력(500m/0도): {int(row['penetration_500m_0deg'])} mm"),
                    ft.Text(f"장갑: 전면 {int(row['front_armor_mm'])} / 측면 {int(row['side_armor_mm'])} / 후면 {int(row['rear_armor_mm'])} mm"),
                ],
                spacing=6,
            )

        def render_table() -> None:
            df = self.service.search_vehicles(
                self._int_or_none(nation_dd.value),
                self._int_or_none(type_dd.value),
                float(br_slider.start_value),
                float(br_slider.end_value),
                keyword_tf.value.strip() if keyword_tf.value else None,
            )
            table_box.content = self._vehicle_table(df, render_detail)
            render_detail(self.selected_vehicle_id)

        def update_br_label(_: ft.ControlEvent | None = None) -> None:
            br_start_text.value = f"{float(br_slider.start_value):.1f}"
            br_end_text.value = f"{float(br_slider.end_value):.1f}"
            self.page.update()

        def search(_: ft.ControlEvent) -> None:
            self.selected_vehicle_id = None
            render_table()
            self.page.update()

        br_slider.on_change = update_br_label
        render_table()
        return self._page_column(
            [
                ft.Text("장비 조회 화면", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        nation_dd,
                        type_dd,
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Text("BR 범위"),
                                    ft.Row([br_start_text, br_slider, br_end_text], spacing=8),
                                ],
                                spacing=4,
                            ),
                            padding=ft.Padding(top=2, right=0, bottom=0, left=0),
                        ),
                        keyword_tf,
                        ft.ElevatedButton("검색", icon=ft.Icons.SEARCH, on_click=search),
                    ],
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row([table_box, detail_box], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            ]
        )

    def _vehicle_form_screen(self) -> ft.Control:
        nations = self.service.list_nations()
        types = self.service.list_vehicle_types()

        name = ft.TextField(label="장비명", width=260)
        nation = ft.Dropdown(label="국가", width=220, options=self._nation_options(nations))
        vehicle_type = ft.Dropdown(label="병과", width=220, options=self._options(types, "type_id", "name"))
        rank = ft.TextField(label="랭크", width=120)
        br = ft.TextField(label="BR", width=120)
        repair = ft.TextField(label="수리비", width=160)
        image_path = ft.TextField(label="이미지 경로", width=420)
        front = ft.TextField(label="정면 장갑(mm)", width=160)
        side = ft.TextField(label="측면 장갑(mm)", width=160)
        rear = ft.TextField(label="후면 장갑(mm)", width=160)
        shell_name = ft.TextField(label="대표 포탄명", width=220)
        shell_type = ft.TextField(label="포탄 종류", width=160)
        penetration = ft.TextField(label="관통력 500m/0도(mm)", width=220)

        def save(_: ft.ControlEvent) -> None:
            try:
                self.service.create_vehicle(
                    {
                        "nation_id": self._required_int(nation.value, "국가"),
                        "type_id": self._required_int(vehicle_type.value, "병과"),
                        "name": self._required_text(name.value, "장비명"),
                        "vehicle_rank": self._required_int(rank.value, "랭크"),
                        "battle_rating": self._required_float(br.value, "BR"),
                        "repair_cost": self._required_int(repair.value, "수리비"),
                        "image_path": image_path.value or "",
                    },
                    {
                        "front_armor_mm": self._required_int(front.value, "정면 장갑"),
                        "side_armor_mm": self._required_int(side.value, "측면 장갑"),
                        "rear_armor_mm": self._required_int(rear.value, "후면 장갑"),
                    },
                    {
                        "name": self._required_text(shell_name.value, "대표 포탄명"),
                        "shell_type": shell_type.value or "",
                        "penetration_500m_0deg": self._required_int(penetration.value, "관통력"),
                    },
                )
                for control in [name, rank, br, repair, image_path, front, side, rear, shell_name, shell_type, penetration]:
                    control.value = ""
                self._show_message("장비 정보가 저장되었습니다.")
            except Exception as exc:
                self._show_message(str(exc), error=True)

        return self._page_column(
            [
                ft.Text("장비 등록 화면", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("탱크 5개 병과만 등록합니다. 관통력은 대표 포탄의 500m/0도 기준 수치입니다."),
                ft.Row([name, nation, vehicle_type], wrap=True),
                ft.Row([rank, br, repair], wrap=True),
                image_path,
                ft.Divider(),
                ft.Text("전차 성능 정보", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([front, side, rear], wrap=True),
                ft.Row([shell_name, shell_type, penetration], wrap=True),
                ft.Row([ft.ElevatedButton("저장", icon=ft.Icons.SAVE, on_click=save), ft.OutlinedButton("취소", on_click=lambda _: self.render())]),
            ]
        )

    def _lineup_screen(self) -> ft.Control:
        nations = self.service.list_nations()
        if self.lineup_nation_id is None and not nations.empty:
            self.lineup_nation_id = int(nations.iloc[0]["nation_id"])

        nation_dd = ft.Dropdown(
            label="국가",
            width=220,
            value=str(self.lineup_nation_id) if self.lineup_nation_id else None,
            options=self._nation_options(nations),
        )
        lineups = self.service.list_lineups(self.lineup_nation_id)
        if self.selected_lineup_id and self.selected_lineup_id not in set(lineups["lineup_id"].astype(int).tolist()):
            self.selected_lineup_id = None
            self.selected_lineup_slot_no = None
            self.selected_lineup_vehicle_id = None
        lineup_match_brs: dict[int, Any] = {}
        if not lineups.empty:
            for lineup_record in lineups.to_dict("records"):
                lineup_id = int(lineup_record["lineup_id"])
                analysis, _ = self.service.lineup_analysis(lineup_id)
                if analysis.empty or pd.isna(analysis.iloc[0]["lineup_battle_rating"]):
                    lineup_match_brs[lineup_id] = "-"
                else:
                    lineup_match_brs[lineup_id] = analysis.iloc[0]["lineup_battle_rating"]

        vehicles = self.service.search_vehicles(nation_id=self.lineup_nation_id)
        lineup_selected = self.selected_lineup_id is not None
        detail_df = self.service.lineup_detail(self.selected_lineup_id) if lineup_selected else pd.DataFrame()
        occupied_vehicle_ids = set(detail_df["vehicle_id"].astype(int).tolist()) if not detail_df.empty else set()
        selected_slot_occupied = False
        if self.selected_lineup_slot_no is not None and not detail_df.empty:
            selected_slot_occupied = bool((detail_df["slot_no"].astype(int) == self.selected_lineup_slot_no).any())
        if not lineup_selected:
            self.selected_lineup_slot_no = None
            self.selected_lineup_vehicle_id = None

        def change_nation(e: ft.ControlEvent) -> None:
            self.lineup_nation_id = self._int_or_none(e.control.value)
            self.selected_lineup_id = None
            self.selected_lineup_slot_no = None
            self.selected_lineup_vehicle_id = None
            self.render()

        def open_create_dialog(_: ft.ControlEvent) -> None:
            title = ft.TextField(label="라인업 이름", width=320)
            mode = ft.Dropdown(
                label="게임 모드",
                width=180,
                value="Realistic",
                options=[ft.dropdown.Option("Arcade"), ft.dropdown.Option("Realistic"), ft.dropdown.Option("Simulator")],
            )

            def create_lineup(_: ft.ControlEvent) -> None:
                try:
                    lineup_id = self.service.create_lineup(
                        self._required_int(nation_dd.value, "국가"),
                        self._required_text(title.value, "라인업 이름"),
                        self._required_text(mode.value, "게임 모드"),
                        1.0,
                    )
                    self.selected_lineup_id = lineup_id
                    self.selected_lineup_slot_no = None
                    self.selected_lineup_vehicle_id = None
                    self.page.pop_dialog()
                    self._show_message("라인업이 생성되었습니다.")
                    self.render()
                except Exception as exc:
                    self._show_message(str(exc), error=True)

            self.page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("라인업 생성"),
                    content=ft.Column(
                        [
                            ft.Text("선택된 국가 기준으로 라인업을 생성합니다."),
                            title,
                            mode,
                        ],
                        tight=True,
                        spacing=12,
                    ),
                    actions=[
                        ft.TextButton("취소", on_click=lambda _: self.page.pop_dialog()),
                        ft.ElevatedButton("생성", icon=ft.Icons.ADD, on_click=create_lineup),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            )

        def select_lineup(lineup_id: int) -> None:
            self.selected_lineup_id = lineup_id
            self.selected_lineup_slot_no = None
            self.selected_lineup_vehicle_id = None
            self.render()

        def select_slot(slot_no: int, vehicle_id: int | None) -> None:
            self.selected_lineup_slot_no = slot_no
            self.selected_lineup_vehicle_id = vehicle_id
            self.render()

        def add_vehicle_to_slot(vehicle_id: int) -> None:
            try:
                if not self.selected_lineup_id:
                    raise ValueError("라인업을 선택해야 합니다.")
                if not self.selected_lineup_slot_no:
                    raise ValueError("장비를 배치할 슬롯을 선택해야 합니다.")
                replacing = selected_slot_occupied
                self.service.add_vehicle_to_lineup(
                    self.selected_lineup_id,
                    vehicle_id,
                    self.selected_lineup_slot_no,
                )
                self.selected_lineup_vehicle_id = vehicle_id
                self._show_message("슬롯의 장비를 교체했습니다." if replacing else "라인업에 장비를 추가했습니다.")
                self.render()
            except Exception as exc:
                self._show_message(str(exc), error=True)

        def remove_vehicle_by_id(vehicle_id: int) -> None:
            try:
                if not self.selected_lineup_id:
                    raise ValueError("라인업을 선택해야 합니다.")
                self.service.remove_vehicle_from_lineup(self.selected_lineup_id, vehicle_id)
                if self.selected_lineup_vehicle_id == vehicle_id:
                    self.selected_lineup_vehicle_id = None
                self._show_message("라인업에서 장비를 제거했습니다.")
                self.render()
            except Exception as exc:
                self._show_message(str(exc), error=True)

        nation_dd.on_select = change_nation

        lineup_list_controls: list[ft.Control] = []
        if lineups.empty:
            lineup_list_controls.append(
                self._empty_state("저장된 라인업이 없습니다.", "라인업 생성 버튼을 눌러 새 라인업을 만드세요.", compact=True)
            )
        else:
            for record in lineups.to_dict("records"):
                lineup_id = int(record["lineup_id"])
                selected = lineup_id == self.selected_lineup_id
                match_br = lineup_match_brs.get(lineup_id, "-")
                lineup_list_controls.append(
                    ft.Container(
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.FORMAT_LIST_BULLETED, color=ft.Colors.CYAN_300 if selected else ft.Colors.GREY_400),
                                ft.Column(
                                    [
                                        ft.Text(str(record["title"]), weight=ft.FontWeight.BOLD),
                                        ft.Row(
                                            [
                                                self._nation_flag_badge(record["nation_name"]),
                                                ft.Text(
                                                    f"{record['nation_name']} / {record['game_mode']} / 매칭 BR {match_br}",
                                                    size=12,
                                                    color=ft.Colors.GREY_400,
                                                ),
                                            ],
                                            spacing=6,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=10,
                        ),
                        bgcolor="#123747" if selected else None,
                        border=ft.Border.all(2 if selected else 1, ft.Colors.CYAN_300 if selected else ft.Colors.GREY_800),
                        border_radius=8,
                        padding=10,
                        on_click=lambda _, lid=lineup_id: select_lineup(lid),
                    )
                )

        left_panel = ft.Container(
            ft.Column(
                [
                    ft.Text("라인업 목록", size=18, weight=ft.FontWeight.BOLD),
                    nation_dd,
                    ft.ElevatedButton("라인업 생성", icon=ft.Icons.ADD, on_click=open_create_dialog, width=240),
                    ft.ListView(lineup_list_controls, spacing=8, height=380),
                ],
                spacing=14,
            ),
            width=300,
            height=620,
            padding=16,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            border_radius=8,
        )

        slot_value = str(self.selected_lineup_slot_no) if self.selected_lineup_slot_no else "-"
        slot_indicator = ft.Container(
            ft.Column(
                [
                    ft.Text("슬롯 번호", size=12, color=ft.Colors.GREY_400),
                    ft.Text(slot_value, size=22, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
            ),
            width=120,
            height=64,
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            border_radius=8,
        )
        add_menu_enabled = lineup_selected and self.selected_lineup_slot_no is not None
        add_menu_label = "교체할 장비" if selected_slot_occupied else "추가할 장비"
        vehicle_add_menu = self._vehicle_add_menu(
            vehicles,
            occupied_vehicle_ids,
            add_menu_enabled,
            add_menu_label,
            add_vehicle_to_slot,
        )
        slot_table = (
            self._lineup_slot_table(detail_df, select_slot, remove_vehicle_by_id)
            if lineup_selected
            else self._empty_state("저장된 라인업을 선택하세요.", "라인업 목록에서 항목을 선택하면 장비 구성이 표시됩니다.")
        )
        right_panel = ft.Container(
            ft.Column(
                [
                    ft.Row([slot_indicator, vehicle_add_menu], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                    slot_table,
                ],
                spacing=14,
            ),
            width=860,
            height=620,
            padding=16,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            border_radius=8,
        )

        return ft.Column(
            [
                ft.Text("라인업 관리 화면", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([left_panel, right_panel], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START),
            ],
            spacing=18,
            scroll=ft.ScrollMode.AUTO,
        )

    def _analysis_screen(self) -> ft.Control:
        nations = self.service.list_nations()
        if self.analysis_nation_id is None and not nations.empty:
            self.analysis_nation_id = int(nations.iloc[0]["nation_id"])

        nation_dd = ft.Dropdown(
            label="국가",
            width=150,
            value=str(self.analysis_nation_id) if self.analysis_nation_id else None,
            options=self._nation_options(nations),
        )
        lineups = self.service.list_lineups(self.analysis_nation_id)
        lineup_dd = ft.Dropdown(
            label="라인업 선택",
            width=280,
            value=str(self.analysis_lineup_id) if self.analysis_lineup_id else None,
            options=self._options(lineups, "lineup_id", "title"),
        )
        detail_df = self.service.lineup_detail(self.analysis_lineup_id) if self.analysis_lineup_id else pd.DataFrame()
        vehicle_dd = ft.Dropdown(
            label="분석할 전차",
            width=360,
            value=str(self.analysis_vehicle_id) if self.analysis_vehicle_id else None,
            options=self._options(detail_df, "vehicle_id", "vehicle_name"),
            disabled=not bool(self.analysis_lineup_id),
        )
        lineup_panel_width = 444
        comparison_section_width = 620
        lineup_panel = ft.Container(
            width=lineup_panel_width,
            padding=16,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
        )
        comparison_panel = ft.Container(
            expand=True,
            padding=16,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
        )

        def render_result() -> None:
            if not self.analysis_lineup_id:
                lineup_panel.content = ft.Column(
                    [
                        ft.Text("라인업 분석", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("라인업을 선택하면 분석 결과가 표시됩니다.", color=ft.Colors.GREY_400),
                    ],
                    spacing=12,
                )
                comparison_panel.content = ft.Column(
                    [
                        ft.Text("매칭 BR 기반 개별 전차 성능 비교", size=18, weight=ft.FontWeight.BOLD),
                        vehicle_dd,
                        ft.Text("라인업을 먼저 선택하세요.", color=ft.Colors.GREY_400),
                    ],
                    spacing=12,
                )
                return
            analysis, type_count = self.service.lineup_analysis(self.analysis_lineup_id)
            summary_controls: list[ft.Control] = []
            if not analysis.empty:
                row = analysis.iloc[0]
                summary_controls = [
                    self._summary_card("매칭 BR", row["lineup_battle_rating"] if pd.notna(row["lineup_battle_rating"]) else "-"),
                    self._summary_card("라인업 평균 BR", row["average_br"] if pd.notna(row["average_br"]) else "-"),
                    self._summary_card("총 수리비", int(row["total_repair_cost"]) if pd.notna(row["total_repair_cost"]) else 0),
                    self._summary_card("장비 수", int(row["vehicle_count"])),
                ]
            comparison_table: ft.Control = ft.Text("전차를 선택하면 개별 성능 비교가 표시됩니다.")
            if self.analysis_vehicle_id:
                comparison = self.service.vehicle_match_analysis(self.analysis_lineup_id, self.analysis_vehicle_id)
                comparison_table = self._comparison_table(comparison)
            summary_grid: ft.Control = ft.Text("라인업 분석 결과가 없습니다.", color=ft.Colors.GREY_400)
            if summary_controls:
                summary_grid = ft.Column(
                    [
                        ft.Row(summary_controls[:2], spacing=10),
                        ft.Row(summary_controls[2:], spacing=10),
                    ],
                    spacing=10,
                )
            lineup_panel.content = ft.Column(
                [
                    ft.Text("라인업 분석", size=18, weight=ft.FontWeight.BOLD),
                    summary_grid,
                    ft.Text("병과별 장비 수", size=18, weight=ft.FontWeight.BOLD),
                    self._type_count_table(type_count),
                ],
                spacing=14,
            )
            comparison_panel.content = ft.Column(
                [
                    ft.Text("매칭 BR 기반 개별 전차 성능 비교", size=18, weight=ft.FontWeight.BOLD),
                    vehicle_dd,
                    ft.Container(comparison_table, width=comparison_section_width),
                ],
                spacing=14,
            )

        def change_nation(e: ft.ControlEvent) -> None:
            self.analysis_nation_id = self._int_or_none(e.control.value)
            self.analysis_lineup_id = None
            self.analysis_vehicle_id = None
            self.render()

        def change_lineup(e: ft.ControlEvent) -> None:
            self.analysis_lineup_id = self._int_or_none(e.control.value)
            self.analysis_vehicle_id = None
            self.render()

        def change_vehicle(e: ft.ControlEvent) -> None:
            self.analysis_vehicle_id = self._int_or_none(e.control.value)
            render_result()
            self.page.update()

        nation_dd.on_select = change_nation
        lineup_dd.on_select = change_lineup
        vehicle_dd.on_select = change_vehicle
        render_result()
        return self._page_column(
            [
                ft.Text("분석 조회 화면", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("라인업 최고 BR을 매칭 BR로 계산하고, ±1.0 범위 전차 평균과 선택 전차를 비교합니다."),
                ft.Row([nation_dd, lineup_dd], spacing=14, width=lineup_panel_width),
                ft.Row(
                    [lineup_panel, comparison_panel],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ]
        )

    def _vehicle_table(self, df: pd.DataFrame, on_select: Any) -> ft.Control:
        if df.empty:
            return ft.Text("조회된 장비가 없습니다.")
        rows = []
        for record in df.to_dict("records"):
            vehicle_id = int(record["vehicle_id"])

            def select(_: ft.ControlEvent, vid: int = vehicle_id) -> None:
                self.selected_vehicle_id = vid
                on_select(vid)
                self.page.update()

            rows.append(
                ft.DataRow(
                    on_select_change=select,
                    cells=[
                        ft.DataCell(ft.Text(str(record["name"]))),
                        ft.DataCell(self._nation_name_control(record["nation"])),
                        ft.DataCell(ft.Text(str(record["vehicle_type"]))),
                        ft.DataCell(ft.Text(str(record["vehicle_rank"]))),
                        ft.DataCell(ft.Text(str(record["battle_rating"]))),
                        ft.DataCell(ft.Text(str(int(record["repair_cost"])))),
                    ],
                )
            )
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(label)) for label in ["장비명", "국가", "병과", "랭크", "BR", "수리비"]],
            rows=rows,
        )

    def _lineup_slot_table(
        self,
        df: pd.DataFrame,
        on_select: Any,
        on_delete: Any | None = None,
    ) -> ft.Control:
        slot_map = {int(record["slot_no"]): record for record in df.to_dict("records")}
        header = ft.Container(
            ft.Row(
                [
                    ft.Text("슬롯", width=72, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("장비명", width=150, weight=ft.FontWeight.BOLD),
                    ft.Text("병과", width=140, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("BR", width=72, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("", width=40),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=34,
            padding=ft.Padding(left=8, top=0, right=8, bottom=0),
            bgcolor=ft.Colors.GREY_900,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=6,
        )
        slot_rows: list[ft.Control] = [header]
        for slot_no in range(1, 11):
            record = slot_map.get(slot_no)
            vehicle_id = int(record["vehicle_id"]) if record else None
            selected = slot_no == self.selected_lineup_slot_no
            delete_control: ft.Control = ft.Text("")
            if record is not None:
                delete_control = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_300,
                    tooltip="장비 제거",
                    on_click=lambda _, vid=vehicle_id: on_delete(vid) if on_delete and vid else None,
                )

            def select(_: ft.ControlEvent, slot: int = slot_no, vid: int | None = vehicle_id) -> None:
                on_select(slot, vid)

            slot_rows.append(
                ft.Container(
                    ft.Row(
                        [
                            ft.Text(str(slot_no), width=72, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text(str(record["vehicle_name"]) if record else "", width=150),
                            ft.Text(str(record["vehicle_type"]) if record else "", width=140, text_align=ft.TextAlign.CENTER),
                            ft.Text(str(record["battle_rating"]) if record else "", width=72, text_align=ft.TextAlign.CENTER),
                            ft.Container(delete_control, width=40, alignment=ft.Alignment.CENTER),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    height=38,
                    padding=ft.Padding(left=8, top=0, right=8, bottom=0),
                    bgcolor="#123747" if selected else "#11161d",
                    border=ft.Border.all(2 if selected else 1, ft.Colors.CYAN_300 if selected else ft.Colors.GREY_800),
                    border_radius=8,
                    on_click=select,
                )
            )
        return ft.Container(
            ft.Column(slot_rows, spacing=4),
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            padding=6,
        )

    def _vehicle_add_menu(
        self,
        vehicles: pd.DataFrame,
        occupied_vehicle_ids: set[int],
        enabled: bool,
        label: str,
        on_add: Any,
    ) -> ft.Control:
        menu_items: list[ft.Control] = []
        available = vehicles
        if not vehicles.empty:
            available = vehicles[~vehicles["vehicle_id"].astype(int).isin(occupied_vehicle_ids)]

        if available.empty:
            empty_text = "교체 가능한 장비 없음" if label.startswith("교체") else "추가 가능한 장비 없음"
            menu_items.append(ft.MenuItemButton(content=empty_text, disabled=True))
        else:
            for record in available.to_dict("records"):
                vehicle_id = int(record["vehicle_id"])
                add_button = ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color=ft.Colors.CYAN_300,
                    tooltip=label,
                    opacity=0,
                    on_click=lambda _, vid=vehicle_id: on_add(vid),
                )

                def hover(e: ft.ControlEvent, button: ft.IconButton = add_button) -> None:
                    button.opacity = 1 if str(e.data).lower() == "true" else 0
                    self.page.update()

                menu_items.append(
                    ft.MenuItemButton(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(str(record["name"]), weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            f"{record['vehicle_type']} / BR {record['battle_rating']}",
                                            size=12,
                                            color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                    spacing=2,
                                )
                            ],
                            width=320,
                        ),
                        trailing=add_button,
                        focus_on_hover=True,
                        on_hover=hover,
                        on_click=lambda _, vid=vehicle_id: on_add(vid),
                    )
                )

        return ft.Container(
            ft.MenuBar(
                controls=[
                    ft.SubmenuButton(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ADD_BOX, color=ft.Colors.CYAN_300 if enabled else ft.Colors.GREY_600),
                                ft.Text(label),
                            ],
                            spacing=8,
                        ),
                        controls=menu_items,
                        disabled=not enabled,
                        width=420,
                    )
                ]
            ),
            width=440,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            border_radius=8,
            padding=4,
        )

    def _type_count_table(self, df: pd.DataFrame) -> ft.Control:
        if df.empty:
            return ft.Text("병과별 장비 수가 없습니다.")
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text("병과")), ft.DataColumn(ft.Text("장비 수"))],
            rows=[
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(r["vehicle_type"]))), ft.DataCell(ft.Text(str(r["type_count"])))])
                for r in df.to_dict("records")
            ],
        )

    def _comparison_table(self, df: pd.DataFrame) -> ft.Control:
        if df.empty:
            return ft.Text("성능 비교 결과가 없습니다.")
        first = df.iloc[0]
        header = ft.Text(
            f"{first['vehicle_name']} (BR {first['vehicle_br']}) / 비교 BR {first['comparison_br_min']:.1f} ~ {first['comparison_br_max']:.1f} / 비교군 {int(first['comparison_count'])}대",
            weight=ft.FontWeight.BOLD,
        )
        penetration_df = df[df["항목"] == "관통력"]
        armor_df = df[df["항목"].astype(str).str.contains("장갑")]
        shell_info = f"대표 포탄: {first['shell_name']} ({first['shell_type']})"
        return ft.Column(
            [
                header,
                self._comparison_section("관통 성능", penetration_df, shell_info=shell_info),
                self._comparison_section("장갑 성능", armor_df),
            ],
            spacing=12,
        )

    def _comparison_section(self, title: str, df: pd.DataFrame, shell_info: str | None = None) -> ft.Control:
        if df.empty:
            return ft.Text(f"{title} 비교 결과가 없습니다.", color=ft.Colors.GREY_500)
        column_widths = [110, 130, 140, 75, 105]
        table_width = sum(column_widths)

        def header_cell(label: str, width: int) -> ft.Control:
            return ft.Container(
                ft.Text(label, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, no_wrap=True),
                width=width,
                padding=ft.Padding(left=4, top=0, right=4, bottom=0),
                alignment=ft.Alignment.CENTER,
            )

        def value_cell(value: str, width: int, align: ft.Alignment = ft.Alignment.CENTER_LEFT) -> ft.Control:
            return ft.Container(
                ft.Text(value, no_wrap=True, size=13),
                width=width,
                padding=ft.Padding(left=4, top=0, right=4, bottom=0),
                alignment=align,
            )

        row_controls: list[ft.Control] = [
            ft.Container(
                ft.Row(
                    [
                        header_cell("항목", column_widths[0]),
                        header_cell("선택 전차", column_widths[1]),
                        header_cell("비교군 평균", column_widths[2]),
                        header_cell("차이", column_widths[3]),
                        header_cell("판정", column_widths[4]),
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=table_width,
                padding=ft.Padding(left=4, top=8, right=4, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_700)),
            )
        ]
        for record in df.to_dict("records"):
            status = str(record["판정"])
            item_label = str(record["항목"])
            row_controls.append(
                ft.Container(
                    ft.Row(
                        [
                            value_cell(item_label, column_widths[0], ft.Alignment.CENTER),
                            value_cell(f"{record['선택 전차']} {record['단위']}", column_widths[1], ft.Alignment.CENTER),
                            value_cell(f"{record['비교군 평균']} {record['단위']}", column_widths[2], ft.Alignment.CENTER),
                            value_cell(f"{record['차이(%)']}%", column_widths[3], ft.Alignment.CENTER),
                            ft.Container(
                                ft.Text(status, no_wrap=True, text_align=ft.TextAlign.CENTER, size=13),
                                width=column_widths[4],
                                bgcolor=self._status_color(status),
                                padding=ft.Padding(left=4, top=6, right=4, bottom=6),
                                border_radius=4,
                                alignment=ft.Alignment.CENTER,
                            ),
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=table_width,
                    padding=ft.Padding(left=4, top=8, right=4, bottom=8),
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_800)),
                )
            )
        section_header: ft.Control = ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_100)
        if shell_info:
            section_header = ft.Row(
                [
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_100),
                    ft.Container(
                        ft.Text(f"{shell_info} / 500m/0도 기준", size=12, color=ft.Colors.GREY_300),
                        expand=True,
                        alignment=ft.Alignment.CENTER_RIGHT,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return ft.Container(
            ft.Column(
                [
                    section_header,
                    ft.Column(row_controls, spacing=0),
                ],
                spacing=6,
            ),
            width=620,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            padding=10,
        )

    def _summary_card(self, label: str, value: Any) -> ft.Control:
        return ft.Container(
            ft.Column([ft.Text(label, color=ft.Colors.GREY_400), ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD)]),
            width=180,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            padding=14,
        )

    def _empty_state(self, title: str, subtitle: str, compact: bool = False) -> ft.Control:
        return ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.INBOX, size=52 if not compact else 36, color=ft.Colors.GREY_500),
                    ft.Text(title, color=ft.Colors.GREY_300, text_align=ft.TextAlign.CENTER),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=16,
        )

    def _page_column(self, controls: list[ft.Control]) -> ft.Control:
        return ft.Column(controls, spacing=18, expand=True, scroll=ft.ScrollMode.AUTO)

    def _nation_options(
        self,
        df: pd.DataFrame,
        all_label: str | None = None,
    ) -> list[ft.dropdown.Option]:
        options: list[ft.dropdown.Option] = []
        if all_label:
            options.append(ft.dropdown.Option(key="", text=all_label))
        for record in df.to_dict("records"):
            name = str(record["name"])
            options.append(
                ft.dropdown.Option(
                    key=str(record["nation_id"]),
                    text=name,
                    content=self._nation_name_control(name),
                )
            )
        return options

    def _nation_name_by_id(self, nations: pd.DataFrame, nation_id: int | None) -> str | None:
        if nation_id is None or nations.empty:
            return None
        matched = nations[nations["nation_id"].astype(int) == int(nation_id)]
        if matched.empty:
            return None
        return str(matched.iloc[0]["name"])

    def _nation_name_control(self, name: Any, text_color: Any = None, size: int = 14) -> ft.Control:
        name_text = str(name)
        return ft.Row(
            [
                self._nation_flag_badge(name_text),
                ft.Text(name_text, color=text_color, size=size),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _vehicle_image_card(self, image_path: Any, title: str) -> ft.Control:
        src = self._resolve_vehicle_image_src(image_path)
        if not src:
            return ft.Container(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=44, color=ft.Colors.GREY_500),
                        ft.Text("이미지 없음", color=ft.Colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                width=320,
                height=170,
                bgcolor="#11161d",
                border=ft.Border.all(1, ft.Colors.GREY_800),
                border_radius=8,
            )
        return ft.Container(
            ft.Image(
                src=src,
                width=320,
                height=170,
                fit=ft.BoxFit.COVER,
            ),
            width=320,
            height=170,
            bgcolor="#11161d",
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    @staticmethod
    def _resolve_vehicle_image_src(image_path: Any) -> str | None:
        raw = ""
        if image_path is not None:
            try:
                raw = "" if pd.isna(image_path) else str(image_path).strip()
            except (TypeError, ValueError):
                raw = str(image_path).strip()
        if raw.lower().startswith(("http://", "https://", "data:image")):
            return raw
        candidates: list[Path] = []
        if raw:
            path = Path(raw)
            candidates.append(path if path.is_absolute() else PROJECT_ROOT / raw)
            if not path.is_absolute():
                candidates.append(PROJECT_ROOT / "assets" / raw)
        candidates.append(DEFAULT_VEHICLE_IMAGE)
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve().as_posix()
        return None

    def _nation_flag_badge(self, name: Any) -> ft.Control:
        name_text = str(name) if name is not None else ""
        normalized = NATION_NAME_ALIASES.get(name_text, name_text)
        border = ft.Border.all(1, ft.Colors.GREY_700)
        flag_path = FLAG_IMAGE_PATHS.get(normalized)
        if flag_path and flag_path.exists():
            return ft.Container(
                ft.Image(
                    src=flag_path.resolve().as_posix(),
                    width=24,
                    height=16,
                    fit=ft.BoxFit.COVER,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        return ft.Container(
            ft.Text("?", size=10, color=ft.Colors.GREY_300, text_align=ft.TextAlign.CENTER),
            width=24,
            height=16,
            bgcolor=ft.Colors.GREY_800,
            border=border,
            border_radius=2,
            alignment=ft.Alignment.CENTER,
        )
        if normalized == "미국":
            stripes = [
                ft.Container(height=2, bgcolor="#b22234" if i % 2 == 0 else "#ffffff")
                for i in range(8)
            ]
            return ft.Container(
                ft.Stack(
                    [
                        ft.Column(stripes, spacing=0),
                        ft.Container(width=11, height=8, bgcolor="#3c3b6e", left=0, top=0),
                    ],
                    width=24,
                    height=16,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "독일":
            return ft.Container(
                ft.Column(
                    [
                        ft.Container(height=5, bgcolor="#111111"),
                        ft.Container(height=5, bgcolor="#dd0000"),
                        ft.Container(height=6, bgcolor="#ffce00"),
                    ],
                    spacing=0,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "소련":
            return ft.Container(
                ft.Text("★", size=9, color="#ffd34d", text_align=ft.TextAlign.CENTER),
                width=24,
                height=16,
                bgcolor="#cc1f1a",
                border=border,
                border_radius=2,
                alignment=ft.Alignment.CENTER,
            )
        if normalized == "영국":
            return ft.Container(
                ft.Stack(
                    [
                        ft.Container(bgcolor="#012169", width=24, height=16),
                        ft.Container(bgcolor="#ffffff", width=24, height=4, left=0, top=6),
                        ft.Container(bgcolor="#ffffff", width=4, height=16, left=10, top=0),
                        ft.Container(bgcolor="#c8102e", width=24, height=2, left=0, top=7),
                        ft.Container(bgcolor="#c8102e", width=2, height=16, left=11, top=0),
                    ],
                    width=24,
                    height=16,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "일본":
            return ft.Container(
                ft.Container(width=8, height=8, bgcolor="#bc002d", shape=ft.BoxShape.CIRCLE),
                width=24,
                height=16,
                bgcolor="#ffffff",
                border=border,
                border_radius=2,
                alignment=ft.Alignment.CENTER,
            )
        if normalized == "중국":
            return ft.Container(
                ft.Text("★", size=9, color="#ffde00", text_align=ft.TextAlign.CENTER),
                width=24,
                height=16,
                bgcolor="#de2910",
                border=border,
                border_radius=2,
                alignment=ft.Alignment.CENTER,
            )
        if normalized == "이탈리아":
            return ft.Container(
                ft.Row(
                    [
                        ft.Container(width=8, height=16, bgcolor="#009246"),
                        ft.Container(width=8, height=16, bgcolor="#ffffff"),
                        ft.Container(width=8, height=16, bgcolor="#ce2b37"),
                    ],
                    spacing=0,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "프랑스":
            return ft.Container(
                ft.Row(
                    [
                        ft.Container(width=8, height=16, bgcolor="#0055a4"),
                        ft.Container(width=8, height=16, bgcolor="#ffffff"),
                        ft.Container(width=8, height=16, bgcolor="#ef4135"),
                    ],
                    spacing=0,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "스웨덴":
            return ft.Container(
                ft.Stack(
                    [
                        ft.Container(bgcolor="#006aa7", width=24, height=16),
                        ft.Container(bgcolor="#fecc00", width=24, height=3, left=0, top=6),
                        ft.Container(bgcolor="#fecc00", width=3, height=16, left=8, top=0),
                    ],
                    width=24,
                    height=16,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        if normalized == "이스라엘":
            return ft.Container(
                ft.Stack(
                    [
                        ft.Container(bgcolor="#ffffff", width=24, height=16),
                        ft.Container(bgcolor="#0038b8", width=24, height=2, left=0, top=2),
                        ft.Container(bgcolor="#0038b8", width=24, height=2, left=0, top=12),
                        ft.Text("✡", size=8, color="#0038b8", left=8, top=3),
                    ],
                    width=24,
                    height=16,
                ),
                width=24,
                height=16,
                border=border,
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        return ft.Container(
            ft.Text("?", size=10, color=ft.Colors.GREY_300, text_align=ft.TextAlign.CENTER),
            width=24,
            height=16,
            bgcolor=ft.Colors.GREY_800,
            border=border,
            border_radius=2,
            alignment=ft.Alignment.CENTER,
        )

    def _options(self, df: pd.DataFrame, key_col: str, label_col: str, all_label: str | None = None) -> list[ft.dropdown.Option]:
        options: list[ft.dropdown.Option] = []
        if all_label:
            options.append(ft.dropdown.Option(key="", text=all_label))
        for record in df.to_dict("records"):
            options.append(ft.dropdown.Option(key=str(record[key_col]), text=str(record[label_col])))
        return options

    def _show_message(self, message: str, error: bool = False) -> None:
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _status_color(self, status: str) -> str:
        return {
            "매우 낮음": "#7f1d1d",
            "낮음": "#b91c1c",
            "약간 낮음": "#ea580c",
            "비슷함": "#ca8a04",
            "약간 높음": "#65a30d",
            "높음": "#15803d",
            "매우 높음": "#166534",
        }.get(status, "#374151")

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        return int(value) if value not in (None, "") else None

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        return float(value) if value not in (None, "") else None

    @staticmethod
    def _required_text(value: Any, label: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError(f"{label} 값을 입력해야 합니다.")
        return str(value).strip()

    @staticmethod
    def _required_int(value: Any, label: str) -> int:
        if value is None or str(value).strip() == "":
            raise ValueError(f"{label} 값을 입력해야 합니다.")
        return int(value)

    @staticmethod
    def _required_float(value: Any, label: str) -> float:
        if value is None or str(value).strip() == "":
            raise ValueError(f"{label} 값을 입력해야 합니다.")
        return float(value)


def main(page: ft.Page) -> None:
    WarThunderApp(page).run()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
