# netflix-tier-Data

[`AIProject-k/netflix-tier`](https://github.com/AIProject-k/netflix-tier) 안드로이드 앱의
**데이터 백엔드**. 넷플릭스 공식 Top 10 TSV를 나라별 작은 JSON으로 가공해 커밋한다.

## 흐름

```
매주 수요일 06:00 UTC (cron) 또는 수동 실행
  └─ scripts/build_data.py
        ├─ https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv     다운로드
        ├─ https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv  다운로드 (~30 MB)
        ├─ 가장 최근 1주치만 추출
        └─ data/latest/ 에 저장
              index.json              week + 국가 목록(코드·이름)
              global.json             글로벌 4개 리스트 (영화·시리즈 × 영어·비영어)
              countries/<ISO2>.json   나라별 영화/시리즈 Top 10

  └─ data/ 변경 있으면 자동 커밋 & push
```

앱은 `raw.githubusercontent.com/AIProject-k/netflix-tier-Data/main/data/latest/*` 를 받는다.

## 필수 레포 설정

1. **이 레포는 Public** 이어야 한다. private면 raw URL이 토큰 없이는 401/404 →
   앱이 데이터를 못 받는다.
2. Settings → Actions → General → **Workflow permissions → Read and write**
   (Actions가 `data/` 를 커밋할 수 있게).
3. 첫 push 후 **Actions 탭 → "Update Netflix Top 10 data" → Run workflow** 한 번 실행.
   (`data/latest/` 에 한 주치가 이미 커밋돼 있어서 앱은 그 전에도 동작한다.)

## 로컬에서 갱신

```bash
python scripts/build_data.py
```

stdlib만 쓴다 (의존성 없음). `curl` 이 있으면 다운로드에 사용하고, 없으면 urllib 폴백.
Python 3.9+.

## 파일

| 경로 | 역할 |
|---|---|
| `scripts/build_data.py` | TSV → JSON 가공 |
| `.github/workflows/update-data.yml` | 주간 자동 갱신 |
| `data/latest/` | 생성물 (앱이 받는 대상) |
