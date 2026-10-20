# SEOUL LIVE — 서울 실시간 도시 상황판

서울시 공공데이터를 지도 위에서 조회하는 첫 번째 MVP입니다. 현재 5개 주요 장소와 실시간 도시데이터의 혼잡도·추정 인구를 지원합니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --reload
```
Windows에서는 `.venv\Scripts\activate`를 사용하세요. 브라우저에서 http://localhost:8000 접속.

기본 `SEOUL_API_KEY=sample`은 서울시 샘플키입니다. 샘플키는 허용된 장소만 조회 가능합니다. 나머지는 별도 인증키가 필요합니다. `.env.example`을 참고하여 운영환경에서 환경변수로 설정하세요. 키를 저장소에 커밋하지 마세요.

## 테스트
```bash
python -m pytest -q
```
실제 외부 API 호출 테스트는 별도 인증키 및 네트워크 허가가 필요합니다. 지도 타일은 외부 CDN을 사용하며 해당 제공자의 약관을 확인해야 합니다.

## 범위
- 지도에서 주요 장소 조회, 장소별 혼잡도·인구 추정치 표시
- 응답 캐싱(5분), API 오류 및 갱신 지연 구분
- 제공 데이터가 없으면 추정값을 만들어내지 않음
- 차기: 공식 API 응답 스모크 테스트, 모듈별 데이터 수집기, 교통·날씨 연동
