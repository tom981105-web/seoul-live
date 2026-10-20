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
