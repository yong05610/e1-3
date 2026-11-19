"""Core MAC calculation and score classification for the Mini NPU Simulator."""

import json
import re
from pathlib import Path
from time import perf_counter


def _validate_matrix(matrix, name):
    """Validate that matrix is a nonempty square sequence of rows."""
    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError(f"{name} must be a nonempty square matrix")

    size = len(matrix)
    for row_index, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) != size:
            raise ValueError(
                f"{name} must be square; row {row_index} must contain {size} values"
            )
        for column_index, value in enumerate(row):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(
                    f"{name}[{row_index}][{column_index}] must be a number"
                )


def mac(matrix_a, matrix_b):
    """Return the MAC score (sum of elementwise products) for two matrices.

    Both inputs must be nonempty, square 2D lists or tuples with matching
    dimensions and numeric values. Raises ValueError for invalid shapes, types,
    or differing dimensions.
    """
    _validate_matrix(matrix_a, "matrix_a")
    _validate_matrix(matrix_b, "matrix_b")
    if len(matrix_a) != len(matrix_b):
        raise ValueError(
            "matrix_a and matrix_b must have the same dimensions "
            f"({len(matrix_a)} != {len(matrix_b)})"
        )

    score = 0
    for row_index in range(len(matrix_a)):
        for column_index in range(len(matrix_a)):
            score += matrix_a[row_index][column_index] * matrix_b[row_index][column_index]
    return score


def classify(score_a, score_b, epsilon=1e-9):
    """Return 'A', 'B', or 'UNDECIDED' for two numeric scores.

    Scores whose absolute difference is strictly less than epsilon are treated
    as tied. Scores and epsilon must be numbers; epsilon must be nonnegative.
    """
    if not isinstance(score_a, (int, float)) or isinstance(score_a, bool):
        raise ValueError("score_a must be a number")
    if not isinstance(score_b, (int, float)) or isinstance(score_b, bool):
        raise ValueError("score_b must be a number")
    if not isinstance(epsilon, (int, float)) or isinstance(epsilon, bool):
        raise ValueError("epsilon must be a number")
    if epsilon < 0:
        raise ValueError("epsilon must be nonnegative")

    difference = abs(score_a - score_b)
    if difference < epsilon:
        return "UNDECIDED"
    if score_a > score_b:
        return "A"
    if score_b > score_a:
        return "B"
    return "UNDECIDED"


def read_matrix(name, size=3):
    """Read a square matrix from the console, retrying invalid rows."""
    matrix = []
    print(f"{name} ({size}줄 입력, 각 줄에 숫자 {size}개)")
    for row_index in range(size):
        while True:
            raw_row = input(f"{row_index + 1}행: ").strip().split()
            if len(raw_row) != size:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                continue
            try:
                row = [float(value) for value in raw_row]
            except ValueError:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                continue
            matrix.append(row)
            break
    return matrix


def display_matrix(name, matrix):
    """Print a labeled matrix for input confirmation."""
    print(f"{name}:")
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


def benchmark_mac(matrix_a, matrix_b, repetitions=10):
    """Return average MAC call time in milliseconds over repeated calls."""
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 10:
        raise ValueError("repetitions must be an integer of at least 10")

    start = perf_counter()
    for _ in range(repetitions):
        mac(matrix_a, matrix_b)
    elapsed = perf_counter() - start
    return elapsed * 1000 / repetitions


def run_user_mode():
    """Collect 3x3 matrices and display MAC scores, timing, and classification."""
    print("\n[필터 입력]")
    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")

    print("\n[입력한 필터 확인]")
    display_matrix("필터 A", filter_a)
    display_matrix("필터 B", filter_b)

    print("\n[패턴 입력]")
    pattern = read_matrix("패턴")

    score_a = mac(filter_a, pattern)
    score_b = mac(filter_b, pattern)
    time_a = benchmark_mac(filter_a, pattern)
    time_b = benchmark_mac(filter_b, pattern)
    result = classify(score_a, score_b)
    labels = {"A": "A", "B": "B", "UNDECIDED": "판정 불가"}

    print("\n[MAC 결과]")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): A {time_a:.6f} ms, B {time_b:.6f} ms")
    print(f"판정: {labels[result]}")


def load_data(path=None):
    """Load and validate the top-level JSON document structure.

    Defaults to data.json beside this source file. File and JSON syntax errors
    are allowed to reach the caller for a user-friendly mode-level message.
    """
    data_path = Path(path) if path is not None else Path(__file__).resolve().parent / "data.json"
    try:
        with data_path.open("r", encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"data.json을 읽을 수 없습니다: {error}") from error

    if not isinstance(data, dict):
        raise ValueError("JSON 최상위 값은 객체여야 합니다.")
    missing_sections = [section for section in ("meta", "filters", "patterns") if section not in data]
    if missing_sections:
        raise ValueError("JSON 필수 항목이 없습니다: " + ", ".join(missing_sections))
    if not isinstance(data["filters"], dict):
        raise ValueError("JSON의 filters 항목은 객체여야 합니다.")
    if not isinstance(data["patterns"], dict):
        raise ValueError("JSON의 patterns 항목은 객체여야 합니다.")
    return data


def normalize_label(label):
    """Normalize supported filter/expected labels to 'Cross' or 'X'."""
    if not isinstance(label, str):
        raise ValueError(f"라벨은 문자열이어야 합니다: {label!r}")
    normalized = label.strip().casefold()
    if normalized in ("+", "cross"):
        return "Cross"
    if normalized == "x":
        return "X"
    raise ValueError(f"알 수 없는 라벨입니다: {label!r}")


def validate_matrix(matrix, expected_size=None, name="행렬"):
    """Validate a numeric square matrix and optionally its required size."""
    if not isinstance(matrix, list) or not matrix:
        raise ValueError(f"{name}은(는) 비어 있지 않은 2차원 배열이어야 합니다.")
    size = len(matrix)
    if expected_size is not None and size != expected_size:
        raise ValueError(f"{name} 행 수가 {size}이며 기대 크기 {expected_size}와 다릅니다.")
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            raise ValueError(f"{name} {row_index + 1}행이 배열이 아닙니다.")
        if len(row) != size:
            raise ValueError(
                f"{name} {row_index + 1}행의 열 수가 {len(row)}이며 행 수 {size}와 다릅니다."
            )
        if expected_size is not None and len(row) != expected_size:
            raise ValueError(
                f"{name} {row_index + 1}행의 열 수가 {len(row)}이며 기대 크기 {expected_size}와 다릅니다."
            )
        for column_index, value in enumerate(row):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(
                    f"{name}[{row_index + 1}][{column_index + 1}] 값이 숫자가 아닙니다."
                )
    return True


def _pattern_size(pattern_id):
    """Extract N from a size_N_idx pattern identifier or raise ValueError."""
    match = re.fullmatch(r"size_(\d+)_(.+)", str(pattern_id).strip())
    if not match:
        raise ValueError("키 형식이 size_N_idx가 아닙니다.")
    return int(match.group(1))


def _normalized_filter_set(raw_filter_set, size):
    """Return validated filters keyed by Cross/X for one pattern size."""
    if not isinstance(raw_filter_set, dict):
        raise ValueError(f"size_{size} 필터 세트가 없거나 객체가 아닙니다.")
    filters = {}
    for raw_label, matrix in raw_filter_set.items():
        try:
            label = normalize_label(raw_label)
        except ValueError:
            continue
        if label in filters:
            raise ValueError(f"{label} 필터 라벨이 중복되었습니다.")
        validate_matrix(matrix, expected_size=size, name=f"{label} 필터")
        filters[label] = matrix
    missing = [label for label in ("Cross", "X") if label not in filters]
    if missing:
        raise ValueError("필터가 없습니다: " + ", ".join(missing))
    return filters


def run_performance_analysis(data, repetitions=10):
    """Print repeated MAC timings for 3x3, 5x5, 13x13, and 25x25."""
    cross_3 = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    x_3 = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
    benchmark_inputs = {3: (cross_3, x_3)}
    unavailable = {}

    # Prepare and validate all benchmark matrices before starting any timing.
    for size in (5, 13, 25):
        try:
            selected_filters = _normalized_filter_set(
                data["filters"].get(f"size_{size}"), size
            )
            benchmark_inputs[size] = (
                selected_filters["Cross"], selected_filters["X"]
            )
        except (ValueError, TypeError, KeyError) as error:
            unavailable[size] = str(error)

    print(f"\n[성능 분석: 평균/{repetitions}회]")
    print(f"{'크기(N×N)':<16}{'평균 시간(ms)':<20}{'연산 횟수(N²)':>16}")
    print("-" * 52)
    for size in (3, 5, 13, 25):
        operations = size * size
        size_label = f"{size}×{size}"
        if size in unavailable:
            print(
                f"{size_label:<16}{'N/A':<20}{operations:>16} "
                f"(측정 불가: {unavailable[size]})"
            )
            continue
        matrix_a, matrix_b = benchmark_inputs[size]
        average_ms = benchmark_mac(matrix_a, matrix_b, repetitions)
        print(f"{size_label:<16}{average_ms:<20.6f}{operations:>16}")


def run_json_mode(data_path=None):
    """Analyze each JSON pattern independently and print case totals."""
    try:
        data = load_data(data_path)
    except ValueError as error:
        print(f"JSON 분석 오류: {error}")
        return

    patterns = data["patterns"]
    total = len(patterns)
    passed = 0
    failed = 0
    failures = []
    filter_cache = {}

    print("\n[JSON 패턴 분석]")
    for pattern_id, case in patterns.items():
        case_name = str(pattern_id)
        try:
            size = _pattern_size(pattern_id)
            if not isinstance(case, dict):
                raise ValueError("사례 항목이 객체가 아닙니다.")
            if "expected" not in case:
                raise ValueError("expected 라벨이 없습니다.")
            if "input" not in case:
                raise ValueError("input 행렬이 없습니다.")
            expected = normalize_label(case["expected"])
            validate_matrix(case["input"], expected_size=size, name="입력 패턴")

            size_key = f"size_{size}"
            if size_key not in filter_cache:
                filter_cache[size_key] = _normalized_filter_set(
                    data["filters"].get(size_key), size
                )
            selected_filters = filter_cache[size_key]
            cross_score = mac(selected_filters["Cross"], case["input"])
            x_score = mac(selected_filters["X"], case["input"])
            raw_result = classify(cross_score, x_score)
            result = {"A": "Cross", "B": "X", "UNDECIDED": "UNDECIDED"}[raw_result]
            is_pass = result != "UNDECIDED" and result == expected
            status = "PASS" if is_pass else "FAIL"
            if is_pass:
                passed += 1
            else:
                failed += 1
                reason = "동점(UNDECIDED)은 expected와 일치해도 PASS가 될 수 없습니다." if result == "UNDECIDED" else "판정이 expected와 다릅니다."
                failures.append((case_name, reason))

            print(f"- {case_name}")
            print(f"  Cross 점수: {cross_score}")
            print(f"  X 점수: {x_score}")
            print(f"  판정: {result} | expected: {expected} | {status}")
            if not is_pass:
                print(f"  실패 사유: {reason}")
        except (ValueError, TypeError, KeyError) as error:
            failed += 1
            reason = str(error)
            failures.append((case_name, reason))
            print(f"- {case_name}: FAIL")
            print(f"  실패 사유: {reason}")

    run_performance_analysis(data)

    print("\n[결과 요약]")
    print(f"총 테스트: {total}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")
    if failures:
        print("실패 케이스:")
        for case_name, reason in failures:
            print(f"- {case_name}: {reason}")


def main():
    """Show the mode menu and run the selected mode."""
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    choice = input("선택: ").strip()

    if choice == "1":
        run_user_mode()
    elif choice == "2":
        run_json_mode()
    else:
        print("잘못된 선택입니다. 프로그램을 종료합니다.")


if __name__ == "__main__":
    main()
