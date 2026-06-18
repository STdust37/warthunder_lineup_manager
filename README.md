# War Thunder Lineup Manager

Flet과 DuckDB를 사용한 워썬더 지상전 라인업 관리 애플리케이션입니다.

## 주요 기능

- 장비 조회: 국가, 병과, BR 범위, 장비명 기준 검색
- 장비 등록: 기본 장비 정보, 장갑 수치, 대표 포탄 관통력 저장
- 국가별 라인업 관리: 하나의 라인업은 하나의 국가 기준으로 구성
- 10개 고정 슬롯 기반 라인업 편집: 슬롯 선택 후 장비 추가 또는 교체
- 분석 조회: 매칭 BR 기준 개별 전차의 관통력과 장갑 비교
- 샘플 데이터: 10개 국가, 50대 지상 장비, 장비별 대표 이미지 경로 포함

## 실행 방법

```powershell
python app.py
```

처음 실행하면 `war_thunder.duckdb` 파일이 생성되고 샘플 데이터가 자동 입력됩니다.

## 검증 방법

```powershell
python smoke_test.py
```

스모크 테스트는 임시 DuckDB 파일을 생성하여 스키마 생성, 초기 데이터 적재, 국가별 라인업 검증, 슬롯 교체, 매칭 BR 기반 분석 기능을 확인합니다.

## 프로젝트 구조

```text
app.py
assets/
  flags/             # 국가 표시용 국기 PNG 이미지
  vehicle_placeholder.svg
  vehicles/          # War Thunder Wiki 기반 샘플 전차 이미지
warthunder_app/
  __init__.py        # 패키지 공개 API
  data_source.py      # 초기 샘플 데이터 Provider 구현체
  database.py         # DuckDB 연결, 스키마 생성, 초기 데이터 적재
  interfaces.py       # Data Provider 및 Repository Interface 명세
  repositories.py     # 테이블별 CRUD 및 Join/분석 쿼리
  services.py         # 유스케이스 단위 비즈니스 로직
```

## 아키텍처 흐름

```text
Flet UI(app.py)
  -> AppService(services.py)
  -> Repository Interface(interfaces.py)
  -> DuckDB Repository(repositories.py)
  -> DuckDB(database.py)

초기 데이터:
SeedDataProviderInterface(interfaces.py)
  -> StaticSeedDataProvider(data_source.py)
  -> database.py
  -> DuckDB
```

## 설계 참고 사항

- `data_source.py`는 예제 프로젝트의 데이터 공급 계층을 참고하여 Provider 구현체로 분리했습니다.
- `interfaces.py`는 최종보고서의 Data Provider Interface 및 Repository Interface 설계와 구현을 대응시키기 위한 명세 파일입니다.
- `services.py`는 구체적인 DuckDB Repository가 아니라 Repository Interface 타입을 기준으로 동작합니다.
- `repositories.py`는 DuckDB SQL을 담당하고, `services.py`는 유스케이스 중심 로직을 담당합니다.
- 분석 조회는 관통 성능과 장갑 성능을 분리하여 표시합니다.

## 적용한 아키텍처 원칙

- 단일 책임 원칙: UI, 서비스, 저장소, 초기 데이터 공급, DB 초기화를 파일별로 분리했습니다.
- 인터페이스 분리 원칙: 국가, 장비, 전차 제원, 포탄, 라인업, 라인업 장비, 분석 조회 저장소를 별도 인터페이스로 정의했습니다.
- 의존성 역전 원칙: `AppService`는 DuckDB 구현체가 아니라 `interfaces.py`의 Protocol에 의존합니다.
- 의존성 주입: `init_database()`는 초기 데이터 Provider를 선택적으로 주입받을 수 있습니다.
- Repository Pattern: SQL 접근 코드는 `repositories.py`에 모아 두고, UI는 Repository를 직접 호출하지 않습니다.
- Service Layer Pattern: 라인업 국가 검증, 슬롯 교체, 매칭 BR 분석 같은 유스케이스 로직은 `services.py`에서 처리합니다.
