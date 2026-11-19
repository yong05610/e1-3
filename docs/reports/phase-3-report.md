# Phase 3 완료 보고서 — data.json 분석 모드

## 1. 변경·추가 파일

- `main.py` — JSON 로드·스키마 검사·라벨 정규화·사례별 판정 기능 추가, 메뉴의 JSON 항목 연결
- `docs/reports/phase-3-report.md` — Phase 3 확인 결과 기록

## 2. JSON 로딩 경로와 스키마 처리

- `load_data(path=None)` 기본 경로는 `Path(__file__).resolve().parent / "data.json"`입니다. 현재 작업 디렉터리와 관계없이 `main.py`가 있는 프로젝트 폴더의 JSON을 읽습니다. 오류 처리를 직접 확인할 수 있도록 선택적 경로 인수도 받습니다.
- JSON 최상위 값은 객체여야 하며 `meta`, `filters`, `patterns`가 있어야 합니다. `filters`와 `patterns`는 객체인지 확인합니다.
- `_pattern_size()`는 `size_N_idx` 형식에서 정수 N을 안전하게 추출합니다. 필터는 해당 `size_N` 그룹에서 읽습니다.
- `normalize_label()`은 공백을 제거하고 대소문자를 무시해 `+`/`cross`를 `Cross`, `x`를 `X`로 통일합니다.
- `validate_matrix()`는 사례 입력과 선택된 필터가 숫자형 정사각 배열이며 키에 명시된 크기 N과 일치하는지 검사합니다.
- `run_json_mode()`는 기존 `mac()`과 `classify()`를 재사용합니다. `UNDECIDED`는 expected와 관계없이 FAIL입니다. 패턴별 예외는 해당 사례의 FAIL 사유로 남기고 다음 사례를 계속 처리합니다.
- JSON 모드에는 Phase 4의 성능 표를 추가하지 않았습니다.

## 3–4. 제공된 data.json 실행 결과 및 라벨

실행 명령:

```powershell
$env:PYTHONIOENCODING='utf-8'; @('2') | python -B main.py
```

실제 케이스 결과:

| 사례 | Cross 점수 | X 점수 | 판정 | expected | 결과 |
|---|---:|---:|---|---|---|
| size_5_1 | 0.9 | 0.8999999999999999 | UNDECIDED | X | FAIL |
| size_5_2 | 8.9 | 0.1 | Cross | Cross | PASS |
| size_13_1 | 0.3 | 14.700000000000008 | X | X | PASS |
| size_13_2 | 7.499999999999997 | 7.5 | UNDECIDED | Cross | FAIL |
| size_25_1 | 4.9 | 4.899999999999999 | UNDECIDED | X | FAIL |
| size_25_2 | 52.9 | 0.1 | Cross | Cross | PASS |

실제 요약 출력은 총 테스트 6, 통과 3, 실패 3이었습니다. 세 FAIL은 점수 차이가 epsilon 미만이라 `UNDECIDED`가 된 사례입니다. 제공 데이터의 expected 라벨 `x`/`+`는 출력에서 `X`/`Cross`로 정규화됐고, 필터 키 `cross`/`x`도 같은 표준 라벨로 선택됐습니다.

대소문자 및 앞뒤 공백 정규화는 아래 직접 호출로 추가 확인했습니다.

```powershell
python -B -c "from main import normalize_label; print(repr(normalize_label(' Cross ')), repr(normalize_label(' X ')), repr(normalize_label(' + ')))"
```

실제 출력:

```text
'Cross' 'X' 'Cross'
```

## 5. 사례 단위 오류 격리 확인

원본 `data.json`은 변경하지 않고 메모리에서 첫 사례의 입력 행 하나를 제거해 임시 JSON 파일로 저장한 뒤 분석했습니다. 실행 절차:

```powershell
python -B -c "import json,tempfile,os; from main import run_json_mode; d=json.load(open('data.json',encoding='utf-8')); d['patterns']['size_5_1']['input'].pop(); f=tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False); json.dump(d,f); f.close(); run_json_mode(f.name); os.unlink(f.name)"
```

실제 결과: `size_5_1`만 `FAIL`로 표시되고 사유에 입력 행 수 4와 기대 크기 5가 출력됐습니다. 이후 `size_5_2`, `size_13_1` 등 나머지 사례도 계속 분석되어 마지막 사례까지 출력됐으며 요약은 총 6, 통과 3, 실패 3이었습니다.

## 6. 잘못된 전체 JSON 처리

잘못된 JSON을 담은 임시 파일로 실행했습니다.

```powershell
python -B -c "import tempfile,os; from main import run_json_mode; f=tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False); f.write('{bad json'); f.close(); run_json_mode(f.name); os.unlink(f.name)"
```

실제 출력:

```text
JSON 분석 오류: data.json을 읽을 수 없습니다: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

traceback 없이 안내 후 반환했습니다.

## 7. Phase 2 사용자 입력 회귀 확인

- 정상 입력을 다시 실행해 A 점수 1.0, B 점수 5.0, 판정 B를 확인했습니다.
- 같은 필터와 0 행렬 입력에서는 A/B 점수 0.0, 판정 불가가 출력됐습니다.
- `a b c`와 `0 1` 행을 순서대로 입력했을 때 숫자 변환 오류 및 열 개수 오류 안내 후 같은 행을 다시 받았고, 정상 결과까지 처리했습니다.
- 측정 출력은 기존처럼 MAC 호출 평균이며, JSON 분석에는 성능 표가 출력되지 않았습니다.

## 8. 미완료 항목 및 결정 필요 사항

- Phase 3 완료 기준을 확인했습니다. PM 추가 결정이 필요한 사항은 없습니다.
- `TASK.md`는 PM 검증 후 갱신 대상이므로 수정하지 않았습니다.
- Phase 4 성능 측정 및 Phase 5 README/최종 리포트는 구현하지 않았습니다.

## 9. 승인 범위 밖 변경

- 없습니다. 기존 사용자 입력 흐름과 Phase 1 계산 함수를 보존하고, Phase 3 JSON 기능만 추가했습니다.
