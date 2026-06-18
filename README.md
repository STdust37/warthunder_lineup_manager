# War Thunder Lineup Manager

Flet과 DuckDB를 사용한 워썬더 지상전 라인업 관리 애플리케이션이다.

## 주요 기능

- 장비 조회: 국가, 병과, BR 범위, 장비명 기준으로 지상 장비를 검색한다.
- 장비 등록: 기본 장비 정보, 장갑 수치, 대표 포탄 관통력을 저장한다.
- 국가별 라인업 관리: 하나의 라인업을 하나의 국가 기준으로 구성한다.
- 10개 고정 슬롯 기반 라인업 편집: 슬롯을 선택한 뒤 장비를 추가하거나 교체한다.
- 분석 조회: 매칭 BR 기준으로 개별 전차의 관통력과 장갑 성능을 비교한다.
- 이미지 출력: DB에 저장된 이미지 경로 또는 URL을 이용해 장비 이미지를 표시한다.

## 실행 방법

```powershell
python app.py
```

처음 실행하면 `war_thunder.duckdb` 파일을 생성하고 샘플 데이터를 자동으로 삽입한다.

## 설치 패키지

```powershell
pip install -r requirements.txt
```

## 프로젝트 구조

```text
app.py
assets/
  flags/                 # 국가 표시용 국기 PNG 이미지
  vehicle_placeholder.svg
  vehicles/              # 샘플 전차 이미지
warthunder_app/
  __init__.py
  data_source.py          # 초기 샘플 데이터 Provider 구현체
  database.py             # DuckDB 연결, 스키마 생성, 초기 데이터 삽입
  interfaces.py           # Data Provider 및 Repository Interface 명세
  repositories.py         # 테이블별 CRUD 및 Join/분석 쿼리
  services.py             # Use Case 단위 비즈니스 로직
```

## 아키텍처 흐름

```text
Flet UI(app.py)
  -> AppService(services.py)
  -> Repository Interface(interfaces.py)
  -> DuckDB Repository(repositories.py)
  -> DuckDB(database.py)

초기 데이터
SeedDataProviderInterface(interfaces.py)
  -> StaticSeedDataProvider(data_source.py)
  -> database.py
  -> DuckDB
```

## 데이터베이스 설계

주요 테이블은 다음과 같다.

- `nation`: 국가 정보를 저장한다.
- `vehicle_type`: 경전차, 중형전차, 중전차, 구축전차, 자주대공포 병과를 저장한다.
- `vehicle`: 장비 기본 정보와 이미지 경로를 저장한다.
- `tank_spec`: 전차의 대표 정면, 측면, 후면 장갑 수치를 저장한다.
- `shell`: 대표 포탄과 500m/0도 기준 관통력을 저장한다.
- `lineup`: 국가별 라인업 정보를 저장한다.
- `lineup_vehicle`: 라인업과 장비의 관계, 슬롯 번호를 저장한다.

## 적용한 설계 원칙

- Repository Pattern: SQL 접근 코드를 `repositories.py`에 모은다.
- Service Layer Pattern: 국가 검증, 슬롯 교체, 매칭 BR 분석 같은 Use Case 로직을 `services.py`에서 처리한다.
- Interface 분리: `interfaces.py`의 Protocol을 기준으로 데이터 공급자와 Repository 계약을 정의한다.
- 의존성 분리: UI는 DuckDB SQL을 직접 호출하지 않고 `AppService`를 통해 기능을 수행한다.
