# SEOUL LIVE — 서울 실시간 도시 상황판

서울시 도시데이터를 GitHub Pages에서 볼 수 있는 정적 웹 프런트엔드와 FastAPI 백엔드 실험 프로젝트입니다.

## GitHub Pages
웹 주소: https://tom981105-web.github.io/seoul-live/

- Settings → Pages → Build and deployment → Source에서 **GitHub Actions**를 선택합니다.
- Actions에서 **Publish Seoul Live to GitHub Pages**를 수동 실행할 수 있습니다.
- 매 30분 GitHub Actions가 공공데이터를 수집해 정적 JSON 스냅샷을 만들고 Pages에 배포합니다(스케줄은 지연될 수 있음).
- Settings → Secrets and variables → Actions → Repository secrets에 `SEOUL_API_KEY`를 넣으면 샘플키 범위를 넘어 장소 데이터를 요청할 수 있습니다.
- 별도 키가 없으면 기본 샘플 장소만 조회를 시도하고, 다른 장소는 **UNAVAILABLE**로 표시합니다.
- API 요청 실패 시에는 가짜 혼잡도 수치를 표시하지 않고 오류 상태를 보여줍니다.

GitHub Pages는 Python 서버를 상시 실행하지 않습니다. 이 공개 버전은 **30분 주기의 스냅샷**이며 즉시 갱신되는 실시간 시스템은 아닙니다. 실시간 열차 도착 등 초단위 데이터는 추후 별도 API 서버가 필요합니다.

## 개발/로컬 API 실행
```bash
pip install -r requirements.txt
uvicorn server.app:app --reload
```
로컬 API는 `/api/places`, `/api/places/{id}/live`를 제공합니다. Pages 웹은 해당 로컬 엔드포인트 대신 정적 JSON을 읽습니다.

## 테스트
```bash
python -m pytest -q
```

## 주요 구조
- `web/index.html`: 정적 지도 웹페이지
- `server/app.py`: 서울시 도시데이터 파서 / 기존 FastAPI
- `scripts/build_pages.py`: 보안키를 공개하지 않고 Pages 배포 데이터를 생성
- `.github/workflows/pages.yml`: 정적 사이트 정기 갱신·배포
- `.github/workflows/ci.yml`: 자동 테스트

## V0.3 — 장소 확장 및 요청량 제한
- 15개 대표 장소로 지도 확장. 좌표는 지도의 대표 지점으로 공식 영역 경계가 아닙니다.
- 공식 장소명 기반의 목록이지만 실제 지원 장소 전체(공식 안내 기준 121곳)는 아직 반영 전입니다.
- GitHub Actions 배포 1회당 최대 15회의 도시데이터 API 요청만 허용하며 요청마다 최소 0.25초 간격을 둡니다.
- 환경변수 `SEOUL_MAX_CALLS`(기본 15)로 더 낮은 호출량을 선택할 수 있습니다.
- 30분 간격으로 최대 15회 요청 시 하루 최대 약 720회(일정이 모두 실행되는 경우)입니다. 제공기관의 계정별 할당량을 먼저 확인하세요.
- 키 미설정 / 호출량 초과 / 응답 오류는 실제 값을 만들어내지 않고 상태로 표시합니다.
