# main.py 호출 구조와 처리 흐름

## 이 도표가 보여 주는 것

이 문서는 `main.py`에서 프로그램이 시작된 뒤 어떤 함수가 호출되고, 입력 방식에 따라 처리가 어떻게 흘러가는지 보여 줍니다. 함수 호출 구조와 처리 순서를 함께 이해하기 위한 흐름도입니다.

유스케이스 다이어그램은 사용자가 할 수 있는 일을 보여 주고, 시퀀스 다이어그램은 시간에 따른 상호작용을 보여 줍니다. 함수 간 호출 관계와 전체 처리 경로를 이해하기 위해 이 문서에서는 흐름도를 사용합니다.

## 전체 흐름도

```mermaid
flowchart TD
    Start["프로그램 시작<br/>__main__"] --> Main["main()"]
    Main --> Choice{"입력 방식 선택"}

    Choice -->|"1: 직접 판정"| User["run_user_mode()"]
    Choice -->|"2: 준비된 사례 확인"| Json["run_json_mode()"]

    subgraph 직접입력["직접 입력 경로"]
        User --> Read["read_matrix()<br/>필터 A, 필터 B, 패턴"]
        Read --> Display["display_matrix()<br/>입력 필터 표시"]
        Display --> UserMac["mac() × 2<br/>A 점수와 B 점수"]
        UserMac --> UserTime["benchmark_mac() × 2<br/>각각 10회 이상 측정"]
        UserTime --> UserClassify["classify()<br/>A / B / UNDECIDED"]
        UserClassify --> UserResult["점수·시간·판정 출력"]
    end

    subgraph JSON분석["JSON 분석 경로"]
        Json --> Load["load_data()<br/>JSON 파일 읽기"]
        Load --> Loop["각 사례 반복"]
        Loop --> Size["_pattern_size()<br/>키에서 N 추출"]
        Size --> Normalize["normalize_label()<br/>expected 라벨 표준화"]
        Normalize --> Validate["validate_matrix()<br/>입력 행렬 크기 확인"]
        Validate --> Filter["_normalized_filter_set()<br/>크기별 필터 정리·검증"]
        Filter --> JsonMac["mac() × 2<br/>Cross 점수와 X 점수"]
        JsonMac --> JsonClassify["classify()<br/>Cross / X / UNDECIDED"]
        JsonClassify --> Compare["expected와 비교<br/>PASS / FAIL"]
        Compare --> Loop
        Loop --> Perf["run_performance_analysis()"]
        Perf --> Bench["benchmark_mac() → mac()<br/>크기별 평균 시간"]
        Bench --> Summary["전체 PASS/FAIL 요약"]
    end

    subgraph 공통계산["공통 계산 함수"]
        Mac["mac()"]
        MatrixCheck["_validate_matrix()<br/>mac 입력 검증"]
        Classify["classify()<br/>epsilon 동점 판정"]
        Benchmark["benchmark_mac()<br/>반복 평균 시간"]
    end

    UserMac -. "필터 A/B, 패턴 → 점수 A/B" .-> Mac
    JsonMac -. "Cross/X 필터, 입력 패턴 → 점수" .-> Mac
    UserClassify -. "점수 A/B → 판정" .-> Classify
    JsonClassify -. "Cross/X 점수 → 판정" .-> Classify
    UserTime -. "필터 A/B, 패턴, 반복 횟수 → 평균 ms" .-> Benchmark
    Bench -. "크기별 필터 쌍, 반복 횟수 → 평균 ms" .-> Benchmark
    Benchmark -. "행렬 쌍을 반복 전달" .-> Mac
    Mac -. "행렬 A/B → 크기·숫자 검증" .-> MatrixCheck
```

점선 화살표는 함수 호출을 나타냅니다. 화살표 글자는 호출할 때 전달하는 값과 반환되는 값을 요약합니다. 실선은 프로그램의 큰 처리 순서를 나타냅니다. 즉, 호출 관계와 데이터 전달을 한 그림에서 함께 읽을 수 있습니다.

## 두 경로의 목적

- **직접 입력 경로:** 사용자가 3×3 필터 두 개와 패턴을 입력하고, 프로그램이 두 점수를 비교해 판정합니다. 미리 정해진 정답 라벨은 없습니다.
- **JSON 분석 경로:** `data.json`에 준비된 패턴들을 판정하고, 각 결과를 `expected`와 비교해 PASS/FAIL을 냅니다. 이 경로는 준비된 사례로 동작을 확인하는 평가 흐름입니다.
- 두 경로는 점수 계산에 `mac()`을, 점수 비교와 동점 처리에 `classify()`를 함께 사용합니다.

## 주요 함수 역할

| 함수 | 역할 |
|---|---|
| `main()` | 입력 경로를 선택하고 해당 처리 함수를 호출합니다. |
| `run_user_mode()` | 사용자가 입력한 필터와 패턴을 판정합니다. |
| `run_json_mode()` | JSON 사례를 반복 처리하고 결과를 채점·요약합니다. |
| `mac()` | 같은 위치의 값을 곱해 모두 더한 점수를 계산합니다. |
| `classify()` | 두 점수를 비교하고 epsilon 범위의 차이는 `UNDECIDED`로 처리합니다. |
| `benchmark_mac()` | MAC 호출을 반복해 평균 시간을 계산합니다. |
| `run_performance_analysis()` | 여러 크기의 MAC 실행 시간을 측정해 출력합니다. |

## 비슷한 이름의 행렬 검증 함수

`_validate_matrix()`와 `validate_matrix()`는 서로 다른 함수입니다.

- `_validate_matrix()`는 `mac()`이 계산을 시작하기 전에 두 입력이 같은 크기의 숫자 행렬인지 확인합니다.
- `validate_matrix()`는 JSON 분석에서 입력 패턴이나 필터가 키에 표시된 예상 크기인지 확인합니다.
