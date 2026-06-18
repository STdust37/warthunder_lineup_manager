from __future__ import annotations

from typing import Any


DEFAULT_VEHICLE_IMAGE_PATH = "assets/vehicle_placeholder.svg"


def wiki_image_path(game_id: str) -> str:
    return f"https://static.encyclopedia.warthunder.com/images/{game_id}.png"


VEHICLE_IMAGE_PATHS = {
    "M2A4": "assets/vehicles/us_m2a4.png",
    "M4A1": "assets/vehicles/us_m4a1_1942_sherman.png",
    "M4A3(76)W": "assets/vehicles/us_m4a3e8_76w_sherman.png",
    "M18 GMC": "assets/vehicles/us_m18_hellcat.png",
    "M1 Abrams": "assets/vehicles/us_m1_abrams.png",
    "M1A2 SEP": "assets/vehicles/us_m1a2_sep_abrams.png",
    "Pz.IV F2": "assets/vehicles/germ_pzkpfw_iv_ausf_f2.png",
    "Tiger H1": "assets/vehicles/germ_pzkpfw_vi_ausf_h1_tiger.png",
    "Panther D": "assets/vehicles/germ_pzkpfw_v_ausf_d_panther.png",
    "Ostwind": "assets/vehicles/germ_flakpanzer_iv_ostwind.png",
    "Leopard 2A6": "assets/vehicles/germ_leopard_2a6.png",
    "Leopard 2A7V": "assets/vehicles/germ_leopard_2a7v.png",
    "T-34 (1942)": "assets/vehicles/ussr_t_34_1942.png",
    "KV-1 (ZiS-5)": "assets/vehicles/ussr_kv_1_zis_5.png",
    "IS-2": "assets/vehicles/ussr_is_2_1943.png",
    "ZSU-37": "assets/vehicles/ussr_zsu_37.png",
    "T-72B3": "assets/vehicles/ussr_t_72b3_2011.png",
    "T-80BVM": "assets/vehicles/ussr_t_80bvm.png",
    "Crusader III": "assets/vehicles/uk_crusader_mk_3.png",
    "Churchill VII": "assets/vehicles/uk_a_22f_mk_7_churchill_1944.png",
    "Centurion Mk 3": "assets/vehicles/uk_centurion_mk_3.png",
    "Challenger 2": "assets/vehicles/uk_challenger_ii.png",
    "Ha-Go": "assets/vehicles/jp_type_95_ha_go.png",
    "Chi-Nu II": "assets/vehicles/jp_type_3_chi_nu_75cm_type_5.png",
    "Type 90": "assets/vehicles/jp_type_90.png",
    "M8 LAC": wiki_image_path("cn_m8_greyhound"),
    "M24 (China)": wiki_image_path("cn_m24_chaffee"),
    "T-34-85 (S-53)": wiki_image_path("cn_t_34_85_d_5t"),
    "WZ305": wiki_image_path("cn_wz_305"),
    "ZTZ99A": wiki_image_path("cn_ztz_99a"),
    "M13/40 (III)": wiki_image_path("it_m13_40_serie_3"),
    "75/18 M41": wiki_image_path("it_semovente_m41_75_18"),
    "M24 (Italy)": wiki_image_path("it_m24_chaffee"),
    "OF-40": wiki_image_path("it_of_40_mk_1"),
    "Ariete": wiki_image_path("it_c1_ariete"),
    "H.35": wiki_image_path("fr_hotchkiss_h35"),
    "B1 bis": wiki_image_path("fr_b1_bis"),
    "M4A4 (SA50)": wiki_image_path("fr_m4a4_cn_75_50"),
    "AMX-13": wiki_image_path("fr_amx_13_75"),
    "Leclerc": wiki_image_path("fr_leclerc_s1"),
    "Strv m/31": wiki_image_path("sw_strv_m31"),
    "Lago I": wiki_image_path("sw_lago_1"),
    "Strv 74": wiki_image_path("sw_strv_74"),
    "Strv 103A": wiki_image_path("sw_strv_103a"),
    "Strv 122A": wiki_image_path("sw_strv_122"),
    "M-51": wiki_image_path("il_m_51"),
    "Magach 3": wiki_image_path("il_magach_3_idf"),
    "Sho't Kal Alef": wiki_image_path("il_centurion_shot_kal_alef"),
    "Merkava Mk.1B": wiki_image_path("il_merkava_mk_1b"),
    "Merkava Mk.4M": wiki_image_path("il_merkava_mk_4m"),
}


def vehicle_image_path(name: str) -> str:
    return VEHICLE_IMAGE_PATHS.get(name, DEFAULT_VEHICLE_IMAGE_PATH)


class StaticSeedDataProvider:
    """고정 샘플 데이터를 공급하는 기본 Provider 구현체."""

    def fetch_nations(self) -> list[tuple[int, str, str]]:
        return fetch_nations()

    def fetch_vehicle_types(self) -> list[tuple[int, str, str]]:
        return fetch_vehicle_types()

    def fetch_vehicle_seed_rows(self) -> list[tuple[Any, ...]]:
        return fetch_vehicle_seed_rows()

    def fetch_lineups(self) -> list[tuple[int, int, str, str, float]]:
        return fetch_lineups()

    def fetch_lineup_vehicles(self) -> list[tuple[int, int, int, str]]:
        return fetch_lineup_vehicles()


def fetch_nations() -> list[tuple[int, str, str]]:
    """초기 국가 기준 데이터를 반환한다."""
    return [
        (1, "미국", ""),
        (2, "독일", ""),
        (3, "소련", ""),
        (4, "영국", ""),
        (5, "일본", ""),
        (6, "중국", ""),
        (7, "이탈리아", ""),
        (8, "프랑스", ""),
        (9, "스웨덴", ""),
        (10, "이스라엘", ""),
    ]


def fetch_vehicle_types() -> list[tuple[int, str, str]]:
    """프로젝트 범위에 포함되는 지상 장비 병과 데이터를 반환한다."""
    return [
        (1, "경전차", "정찰과 기동성이 강한 경전차"),
        (2, "중형전차", "화력, 장갑, 기동성의 균형이 좋은 중형전차"),
        (3, "중전차", "장갑과 화력이 강한 중전차"),
        (4, "구축전차", "대전차 화력에 특화된 구축전차"),
        (5, "자주대공포", "항공기 격추를 위한 자주대공포"),
    ]


def fetch_vehicle_seed_rows() -> list[tuple[Any, ...]]:
    """초기 전차, 장갑, 대표 포탄 데이터를 한 번에 반환한다."""
    image = DEFAULT_VEHICLE_IMAGE_PATH
    rows = [
        # id, nation, type, name, rank, br, repair, image, front, side, rear, shell, shell_type, pen
        (1, 1, 1, "M2A4", 1, 1.0, 410, image, 25, 25, 25, "M51B1", "APCBC", 55),
        (2, 1, 2, "M4A1", 2, 3.3, 1250, image, 51, 38, 38, "M61 shot", "APCBC", 88),
        (3, 1, 2, "M4A3(76)W", 4, 5.3, 2850, image, 63, 38, 38, "M62 shell", "APCBC", 128),
        (4, 1, 4, "M18 GMC", 3, 5.7, 2200, image, 13, 13, 13, "M62 shell", "APCBC", 128),
        (5, 1, 2, "M1 Abrams", 6, 10.3, 7200, image, 350, 90, 45, "M774", "APFSDS", 360),
        (6, 1, 2, "M1A2 SEP", 7, 11.7, 8900, image, 430, 120, 60, "M829A2", "APFSDS", 520),
        (7, 2, 2, "Pz.IV F2", 2, 3.3, 980, image, 50, 30, 20, "PzGr 39", "APCBC", 106),
        (8, 2, 3, "Tiger H1", 3, 5.7, 3400, image, 100, 80, 80, "PzGr 39", "APCBC", 145),
        (9, 2, 2, "Panther D", 3, 5.3, 3100, image, 80, 40, 40, "PzGr 39/42", "APCBC", 149),
        (10, 2, 5, "Ostwind", 3, 4.0, 1600, image, 80, 30, 20, "PzGr", "API-T", 48),
        (11, 2, 2, "Leopard 2A6", 7, 11.7, 8700, image, 440, 120, 60, "DM53", "APFSDS", 560),
        (12, 2, 2, "Leopard 2A7V", 8, 12.0, 9300, image, 500, 150, 80, "DM53", "APFSDS", 560),
        (13, 3, 2, "T-34 (1942)", 2, 3.7, 1300, image, 45, 45, 40, "BR-350B", "APHEBC", 86),
        (14, 3, 3, "KV-1 (ZiS-5)", 2, 4.7, 2100, image, 75, 75, 70, "BR-350B", "APHEBC", 86),
        (15, 3, 3, "IS-2", 4, 6.0, 3900, image, 120, 90, 60, "BR-471B", "APHEBC", 170),
        (16, 3, 5, "ZSU-37", 3, 3.7, 1500, image, 15, 15, 10, "BR-167P", "APCR", 64),
        (17, 3, 2, "T-72B3", 7, 11.3, 8200, image, 410, 110, 60, "3BM60", "APFSDS", 532),
        (18, 3, 2, "T-80BVM", 7, 11.7, 8800, image, 450, 120, 60, "3BM60", "APFSDS", 532),
        (19, 4, 1, "Crusader III", 2, 2.7, 900, image, 40, 28, 28, "Shot Mk.8", "APCBC", 84),
        (20, 4, 3, "Churchill VII", 3, 4.7, 2500, image, 152, 95, 50, "Shot Mk.9", "APCBC", 91),
        (21, 4, 2, "Centurion Mk 3", 5, 7.7, 4200, image, 152, 51, 38, "Shot Mk.3", "APDS", 250),
        (22, 4, 2, "Challenger 2", 7, 11.3, 8600, image, 430, 110, 55, "L27A1", "APFSDS", 530),
        (23, 5, 1, "Ha-Go", 1, 1.0, 350, image, 12, 12, 10, "Type 94 APHE", "APHE", 35),
        (24, 5, 2, "Chi-Nu II", 3, 4.3, 1700, image, 50, 25, 20, "Type 4 Kou", "APHE", 125),
        (25, 5, 2, "Type 90", 7, 11.0, 8200, image, 390, 100, 50, "JM33", "APFSDS", 470),
        (26, 6, 1, "M8 LAC", 1, 1.0, 380, image, 19, 10, 10, "M51", "APCBC", 71),
        (27, 6, 1, "M24 (China)", 2, 3.7, 1300, image, 25, 25, 19, "M61 shot", "APCBC", 88),
        (28, 6, 2, "T-34-85 (S-53)", 4, 5.7, 3600, image, 45, 45, 40, "BR-365A", "APHEBC", 125),
        (29, 6, 5, "WZ305", 5, 8.0, 5200, image, 15, 15, 10, "BR-281U", "APHE", 64),
        (30, 6, 2, "ZTZ99A", 8, 12.0, 9300, image, 550, 100, 50, "DTC10-125", "APFSDS", 577),
        (31, 7, 2, "M13/40 (III)", 1, 1.7, 450, image, 30, 25, 25, "Granata Perforante mod.39", "APHE", 49),
        (32, 7, 4, "75/18 M41", 2, 2.3, 850, image, 50, 25, 25, "Effetto Pronto mod.42", "HEAT", 100),
        (33, 7, 1, "M24 (Italy)", 3, 3.7, 1350, image, 25, 25, 19, "M61 shot", "APCBC", 88),
        (34, 7, 2, "OF-40", 6, 8.0, 5200, image, 70, 35, 25, "DM23", "APFSDS", 337),
        (35, 7, 2, "Ariete", 8, 11.3, 9000, image, 580, 80, 40, "CL3143", "APFSDS", 589),
        (36, 8, 1, "H.35", 1, 1.0, 320, image, 34, 34, 22, "Mle 1935", "APC", 36),
        (37, 8, 3, "B1 bis", 2, 2.3, 1200, image, 60, 55, 55, "Mle 1935", "APC", 66),
        (38, 8, 2, "M4A4 (SA50)", 3, 5.0, 2800, image, 63, 38, 38, "PCOT-51P", "APCBC", 182),
        (39, 8, 1, "AMX-13", 4, 6.7, 3500, image, 40, 20, 15, "PCOT-51P", "APCBC", 182),
        (40, 8, 2, "Leclerc", 8, 12.0, 9400, image, 500, 80, 40, "OFL 120 F1", "APFSDS", 575),
        (41, 9, 1, "Strv m/31", 1, 1.0, 360, image, 14, 14, 14, "slpprj m/38", "APCBC", 55),
        (42, 9, 2, "Lago I", 2, 2.7, 950, image, 34, 24, 24, "slpprj m/40", "APCBC", 71),
        (43, 9, 2, "Strv 74", 3, 5.7, 2700, image, 55, 30, 20, "slpprj m/49", "APCBC", 145),
        (44, 9, 4, "Strv 103A", 5, 8.0, 4700, image, 40, 35, 30, "slpprj m/62", "APDS", 300),
        (45, 9, 2, "Strv 122A", 8, 12.0, 9500, image, 520, 120, 60, "slpprj m/95", "APFSDS", 589),
        (46, 10, 2, "M-51", 4, 6.0, 3200, image, 51, 38, 38, "OCC 105 F1", "HEATFS", 400),
        (47, 10, 2, "Magach 3", 5, 7.7, 4300, image, 110, 76, 35, "M728", "APDS", 260),
        (48, 10, 2, "Sho't Kal Alef", 5, 8.0, 4700, image, 152, 51, 38, "M392A2", "APDS", 300),
        (49, 10, 2, "Merkava Mk.1B", 6, 9.3, 6200, image, 250, 80, 40, "M111", "APFSDS", 337),
        (50, 10, 2, "Merkava Mk.4M", 8, 12.0, 9500, image, 450, 100, 50, "M338", "APFSDS", 540),
    ]
    return [
        (*row[:7], vehicle_image_path(str(row[3])), *row[8:])
        for row in rows
    ]


def fetch_lineups() -> list[tuple[Any, ...]]:
    """초기 샘플 라인업 데이터를 반환한다."""
    return [
        (1, 2, "독일 5.7 지상 라인업", "Realistic", 5.7),
        (2, 2, "독일 BR 혼합 테스트", "Realistic", 11.7),
        (3, 1, "미국 5.7 지상 라인업", "Realistic", 5.7),
    ]


def fetch_lineup_vehicles() -> list[tuple[int, int, int, str]]:
    """초기 샘플 라인업 슬롯 데이터를 반환한다."""
    return [
        (1, 8, 1, "주력 중전차"),
        (1, 9, 2, "중형전차"),
        (1, 10, 3, "대공 방어"),
        (2, 7, 1, "낮은 BR 테스트 장비"),
        (2, 11, 2, "라인업 최고 BR 장비"),
        (3, 3, 1, "주력 중형전차"),
        (3, 4, 2, "기동형 구축전차"),
    ]
