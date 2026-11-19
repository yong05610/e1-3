# Phase 1 완료 보고서 — 핵심 MAC 계산과 판정

## 1. 변경·추가 파일

- `main.py` — MAC 계산과 점수 판정 함수 구현
- `docs/reports/phase-1-report.md` — Phase 1 완료 보고서

## 2. 구현 내용

- `mac(matrix_a, matrix_b)`는 같은 크기의 비어 있지 않은 정사각형 2차원 리스트/튜플을 받아 중첩 반복문으로 위치별 곱의 합을 반환합니다.
- 행렬이 비었거나 정사각형이 아니거나, 숫자가 아닌 값이 있으면 구체적인 사유를 담은 `ValueError`를 발생시킵니다.
- 두 입력의 크기가 다르면 크기 불일치 내용을 담은 `ValueError`를 발생시킵니다.
- `classify(score_a, score_b, epsilon=1e-9)`는 A 점수가 높으면 `A`, B 점수가 높으면 `B`, 동점이면 `UNDECIDED`를 반환합니다.
- `abs(score_a - score_b) < epsilon`이면 동점으로 처리합니다. 기준이 엄격한 `<`이므로 차이가 epsilon과 정확히 같으면 동점이 아닙니다.
- 점수는 숫자여야 하고 epsilon은 0 이상이어야 하며, 조건 위반 시 `ValueError`를 발생시킵니다.
- 외부 라이브러리, 클래스, 자동 테스트 파일은 추가하지 않았습니다.

## 3–4. 직접 확인한 명령과 결과

명령:

```powershell
python -c "from main import mac, classify; cross=[[0,1,0],[1,1,1],[0,1,0]]; x=[[1,0,1],[0,1,0],[1,0,1]]; print('cross_score=', mac(cross, cross)); print('x_score=', mac(cross, x)); print('tie_sub_epsilon=', classify(1.0, 1.0 + 5e-10)); print('winner_over_epsilon=', classify(5.0, 1.0)); print('epsilon_boundary=', classify(0.0, 1e-9))"
```

실제 출력:

```text
cross_score= 5
x_score= 1
tie_sub_epsilon= UNDECIDED
winner_over_epsilon= A
epsilon_boundary= B
```

완료 기준별 결과:

| 확인 항목 | 기대 결과 | 실제 결과 |
|---|---|---|
| 십자가 입력 × 십자가 필터 | 5 | 5 — 통과 |
| 십자가 입력 × X 필터 | 1 | 1 — 통과 |
| epsilon 미만 점수 차 | `UNDECIDED` | `UNDECIDED` — 통과 |
| epsilon 초과 점수 차 | 높은 점수 쪽 | `A` — 통과 |
| epsilon과 같은 점수 차 (`classify(0.0, 1e-9)`) | `< epsilon` 조건에 해당하지 않으므로 높은 점수 쪽 `B` | `B` — 통과 |

오류 정책 명령:

```powershell
python -c "from main import mac; exec('for name, a, b in [(\'empty\', [], []), (\'non_square\', [[1,2]], [[1,2]]), (\'dimension_mismatch\', [[1]], [[1,2],[3,4]])]:\n try:\n  mac(a,b)\n except ValueError as e:\n  print(name + \' : ValueError: \' + str(e))')"
```

실제 출력:

```text
empty : ValueError: matrix_a must be a nonempty square matrix
non_square : ValueError: matrix_a must be square; row 0 must contain 1 values
dimension_mismatch : ValueError: matrix_a and matrix_b must have the same dimensions (1 != 2)
```

외부 수치 라이브러리 사용 여부는 `rg -n "numpy|pandas|^import |^from " main.py`로 확인했습니다. 출력이 없어 표준 라이브러리 외 import가 없습니다.

## 5. 미완료 항목 및 결정 필요 사항

- Phase 1 완료 기준에 미완료 항목은 없습니다.
- PM의 추가 결정이 필요한 사항은 없습니다.
- `TASK.md`의 Phase 1 완료/통과 표시는 PM 독립 검증 이후에 갱신하도록 그대로 두었습니다.
- 자동 테스트 파일이나 프레임워크는 추가하지 않았습니다. 확인은 지시서에 맞춰 직접 실행 명령으로 수행했습니다.

## 6. 승인 범위 밖 변경

- 없습니다. 메뉴, 사용자 입력, JSON 분석, 벤치마크, README 및 후속 Phase 작업은 구현하지 않았습니다.
