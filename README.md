# netflix-tier-Data

넷플릭스 공식 Top 10 데이터를 가공해 커밋하는 레포. 두 갈래가 있다:

1. **앱 데이터** — [`AIProject-k/netflix-tier`](https://github.com/AIProject-k/netflix-tier)
   안드로이드 앱이 받는 이번 주 Top 10 (`data/latest/`).
2. **N100 실험 랭킹** — 최근 26주 Top 10을 누적해 자체 산정한 한국 TOP 100
   (`data/n100/`). **공식 넷플릭스 순위 아님.**

## 흐름

```
매주 수요일 06:00 UTC (cron) 또는 수동 실행
  ├─ scripts/build_data.py       ← 앱 데이터. 가장 최근 1주치만.
  │     data/latest/{index,global}.json, countries/<ISO2>.json  (93개국)
  │
  ├─ scripts/build_history.py    ← 2021~현재 전체 주차 누적 (덮어쓰지 않음)
  │     data/history/global.json
  │     data/history/countries/<CC>.json   (KR US JP GB BR MX FR DE IN TW)
  │
  └─ scripts/build_n100.py       ← history 읽어서 점수 계산 (재다운로드 없음)
        data/n100/kr.json         all / films / tv 각 최대 100
```

`data/latest/` 는 앱이 의존하므로 형식·동작을 그대로 둔다. `build_history.py` /
`build_n100.py` 는 순수 추가분.

앱은 `raw.githubusercontent.com/AIProject-k/netflix-tier-Data/main/data/latest/*` 를 받는다.

## N100 점수 (v1)

명세: [`docs/n100-score-v1.md`](docs/n100-score-v1.md). 요약:

```
N100 = 0.40·순위점수 + 0.20·최신성 + 0.15·장기성 + 0.15·상승세 + 0.10·글로벌
```

- 후보군: 최근 26주(`WINDOW_WEEKS`) 안에 KR 영화/시리즈 Top 10에 1회 이상 등장한 작품
- 작품 정규화: `show_title` + 매체구분으로 그룹핑 (시즌은 `season_title` 로 이미 분리돼 있어 대부분 자동 병합)
- 모든 상수는 `scripts/n100/config.py`. 바꾸고 `build_n100.py` 만 다시 돌리면 됨 (재다운로드 X)

현재 26주 실측: KR 고유 작품 영화 124 / 시리즈 80 / 합계 204 →
**ALL·영화는 100개 채워지고 시리즈는 80개까지**. 시즌 중복은 4건.

## 필수 레포 설정

1. **이 레포는 Public** 이어야 한다 (private면 raw URL 401/404).
2. Settings → Actions → General → **Workflow permissions → Read and write**.
3. 첫 push 후 **Actions 탭 → "Update Netflix Top 10 data" → Run workflow** 한 번.

## 로컬에서 갱신

```bash
python scripts/build_data.py     # 앱 데이터
python scripts/build_history.py   # 이력 누적 (~30 MB 다운로드)
python scripts/build_n100.py      # N100 계산 (history 필요)
```

stdlib만 쓴다 (의존성 없음). `curl` 있으면 사용, 없으면 urllib 폴백. Python 3.9+.

## 파일

| 경로 | 역할 |
|---|---|
| `scripts/build_data.py` | TSV → 이번 주 앱 데이터 |
| `scripts/build_history.py` | TSV → 전체 주차 이력 (10개국 + 글로벌) |
| `scripts/build_n100.py` | 이력 → N100 TOP 100 |
| `scripts/n100/` | `config.py` (상수) · `normalize.py` (작품 키) · `score.py` (공식) |
| `docs/n100-score-v1.md` | 점수 공식 명세 |
| `data/latest/` | 앱이 받는 대상 |
| `data/history/` | 원본 주차 누적 (덮어쓰지 않음) |
| `data/n100/kr.json` | N100 실험 랭킹 |
