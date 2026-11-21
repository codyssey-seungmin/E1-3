import time
import json
from pathlib import Path


EPSILON = 1e-9


def calculate_mac(pattern, filter_data):
    """같은 위치의 곱을 누적하며, 동일한 비교 조건에서 점수가 클수록 더 유사하다고 해석한다."""
    total = 0.0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_data[row][col]

    return total

def compare_scores(score_a, score_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"

    if score_a > score_b:
        return "A"

    return "B"

def generate_patterns(size):
    if type(size) is not int or size < 1:
        raise ValueError("패턴 크기는 1 이상의 정수여야 합니다.")

    cross = []
    x_shape = []
    center = size // 2

    for row in range(size):
        cross_row = []
        x_row = []
        for col in range(size):
            cross_row.append(1 if row == center or col == center else 0)
            x_row.append(1 if row == col or row + col == size - 1 else 0)
        cross.append(cross_row)
        x_shape.append(x_row)

    return {"Cross": cross, "X": x_shape}


def print_matrix(name, matrix):
    print(f"\n[{name}]")
    for row in matrix:
        print(" ".join(str(value) for value in row))


def read_matrix(name):
    print(f"{name}을 3줄로 입력하세요. 숫자는 공백으로 구분하세요.")
    print("자동 생성하려면 첫 줄에 Cross 또는 X를 입력하세요.")
    matrix = []

    for row in range(3):
        while True:
            parts = input(f"{row + 1}번째 줄: ").split()

            if row == 0 and len(parts) == 1 and parts[0].lower() in ("+", "cross", "x"):
                label = normalize_label(parts[0])
                matrix = generate_patterns(3)[label]
                print_matrix(f"{name}: {label} 자동 생성", matrix)
                return matrix

            if len(parts) != 3:
                print("숫자 3개를 입력해 주세요.")
                continue

            try:
                values = [float(part) for part in parts]
            except ValueError:
                print("숫자만 입력해 주세요.")
                continue

            matrix.append(values)
            break

    return matrix

def measure_mac_time(pattern, filter_data):
    total_time = 0.0

    for repeat in range(10):
        start = time.perf_counter()
        calculate_mac(pattern, filter_data)
        end = time.perf_counter()

        total_time += end - start

    return total_time / 10 * 1000

def normalize_label(label):
    label = label.strip().lower()

    if label in ("+", "cross"):
        return "Cross"

    if label == "x":
        return "X"

    raise ValueError(f"알 수 없는 라벨: {label}")

def load_data():
    path = Path(__file__).parent / "data.json"

    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("data.json 파일을 main.py와 같은 폴더에 넣어 주세요.")
        return None
    except (json.JSONDecodeError, UnicodeError):
        print("data.json의 JSON 형식이나 문자 인코딩을 확인해 주세요.")
        return None
    except OSError as error:
        print(f"파일을 읽을 수 없습니다: {error}")
        return None

    return data

def validate_matrix(matrix, size):
    if not isinstance(matrix, list) or len(matrix) != size:
        raise ValueError(f"행 개수가 {size}개여야 합니다.")

    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(f"각 행의 숫자가 {size}개여야 합니다.")

        for value in row:
            if type(value) not in (int, float):
                raise ValueError("표에는 숫자만 들어가야 합니다.")

def get_filters(dataset, size):
    raw_filters = dataset["filters"][f"size_{size}"]

    if not isinstance(raw_filters, dict):
        raise ValueError("필터는 이름과 표를 묶은 딕셔너리여야 합니다.")

    filters = {}

    for label, matrix in raw_filters.items():
        standard_label = normalize_label(label)
        validate_matrix(matrix, size)

        if standard_label in filters:
            raise ValueError(f"필터 이름이 중복됩니다: {standard_label}")

        filters[standard_label] = matrix

    if "Cross" not in filters or "X" not in filters:
        raise ValueError("Cross와 X 필터가 모두 필요합니다.")

    return filters

def get_pattern_size(case_id):
    parts = case_id.split("_")

    if len(parts) != 3 or parts[0] != "size":
        raise ValueError("패턴 이름은 size_N_idx 형식이어야 합니다.")

    if not parts[1].isdigit() or not parts[2].isdigit():
        raise ValueError("패턴 크기와 번호는 양의 정수여야 합니다.")

    size = int(parts[1])

    if size < 1 or int(parts[2]) < 1:
        raise ValueError("패턴 크기와 번호는 1 이상이어야 합니다.")

    return size

def analyze_pattern(dataset, case_id, case):
    size = get_pattern_size(case_id)
    filters = get_filters(dataset, size)

    if not isinstance(case, dict):
        raise ValueError("패턴 정보는 딕셔너리여야 합니다.")

    pattern = case["input"]
    validate_matrix(pattern, size)

    if not isinstance(case["expected"], str):
        raise ValueError("expected는 문자열이어야 합니다.")

    expected = normalize_label(case["expected"])

    cross_score = calculate_mac(pattern, filters["Cross"])
    x_score = calculate_mac(pattern, filters["X"])

    decision = compare_scores(cross_score, x_score)
    labels = {"A": "Cross", "B": "X", "UNDECIDED": "UNDECIDED"}
    predicted = labels[decision]

    return {
        "cross_score": cross_score,
        "x_score": x_score,
        "predicted": predicted,
        "expected": expected,
        "passed": predicted == expected,
    }

def analyze_all_patterns(dataset):
    if not isinstance(dataset, dict):
        raise ValueError("전체 데이터는 딕셔너리여야 합니다.")

    patterns = dataset.get("patterns")

    if not isinstance(patterns, dict):
        raise ValueError("patterns는 딕셔너리여야 합니다.")

    results = []

    for case_id, case in patterns.items():
        try:
            result = analyze_pattern(dataset, case_id, case)

            print(f"\n--- {case_id} ---")
            print("Cross 점수:", result["cross_score"])
            print("X 점수:", result["x_score"])
            print("판정:", result["predicted"])
            print("expected:", result["expected"])

            if result["passed"]:
                result["reason"] = ""
            elif result["predicted"] == "UNDECIDED":
                result["reason"] = "허용오차 기준 동점으로 판정 불가"
            else:
                result["reason"] = "판정 결과와 expected가 다름"

        except (KeyError, ValueError, TypeError) as error:
            result = {
                "passed": False,
                "reason": f"데이터 검증 오류: {error}",
            }

        result["case_id"] = case_id
        results.append(result)

        if result["passed"]:
            print("PASS")
        else:
            print("FAIL -", result["reason"])

    return results

def print_summary(results):
    total = len(results)
    passed = 0
    failures = []

    for result in results:
        if result["passed"]:
            passed += 1
        else:
            failures.append(result)

    print("\n[결과 요약]")
    print("총 테스트:", total)
    print("통과:", passed)
    print("실패:", len(failures))

    if failures:
        print("\n실패 케이스:")
        for result in failures:
            print(f"- {result['case_id']}: {result['reason']}")
    else:
        print("모든 케이스가 통과했습니다.")

def print_performance(dataset):
    print("\n[성능 분석: MAC 1회 기준, 10회 평균]")
    print("크기 | 평균 시간(ms) | 연산 횟수(N²)")

    for size in (3, 5, 13, 25):
        try:
            if size == 3:
                matrix = generate_patterns(size)["Cross"]
            else:
                filters = get_filters(dataset, size)
                matrix = filters["Cross"]

            average_ms = measure_mac_time(matrix, matrix)
            print(f"{size}×{size} | {average_ms:.6f} | {size * size}")

        except (KeyError, ValueError, TypeError) as error:
            print(f"{size}×{size} | 측정 불가 | {size * size}")
            print(f"사유: {error}")

def run_manual_mode():
    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")
    print("필터 A와 B 저장 완료")

    pattern = read_matrix("패턴")

    score_a = calculate_mac(pattern, filter_a)
    score_b = calculate_mac(pattern, filter_b)

    print("A 점수:", score_a)
    print("B 점수:", score_b)
    print("판정:", compare_scores(score_a, score_b))

    average_ms = measure_mac_time(pattern, filter_a)

    print("\n[성능 분석: MAC 함수 1회 기준, 10회 평균]")
    print("크기 | 평균 시간(ms) | 연산 횟수(N²)")
    print(f"3×3 | {average_ms:.6f} | 9")

def run_generator_mode():
    while True:
        try:
            size = int(input("패턴 크기 N (1 이상의 정수): "))
            filters = generate_patterns(size)
            break
        except ValueError as error:
            print(f"입력 오류: {error}")

    for label, pattern in filters.items():
        print_matrix(f"{size}×{size} {label}", pattern)
        cross_score = calculate_mac(pattern, filters["Cross"])
        x_score = calculate_mac(pattern, filters["X"])
        decision = compare_scores(cross_score, x_score)
        labels = {"A": "Cross", "B": "X", "UNDECIDED": "UNDECIDED"}
        print("Cross 점수:", cross_score)
        print("X 점수:", x_score)
        print("판정:", labels[decision])

    average_ms = measure_mac_time(filters["Cross"], filters["Cross"])
    print("\n[성능 분석: MAC 1회 기준, 10회 평균]")
    print("크기 | 평균 시간(ms) | 연산 횟수(N²)")
    print(f"{size}×{size} | {average_ms:.6f} | {size * size}")


def run_json_mode():
    dataset = load_data()

    if dataset is None:
        return

    print("\n[필터 로드]")
    for size in (5, 13, 25):
        try:
            get_filters(dataset, size)
            print(f"size_{size} 필터 로드 완료 (Cross, X)")
        except (KeyError, ValueError, TypeError) as error:
            print(f"size_{size} 필터 오류: {error}")

    try:
        results = analyze_all_patterns(dataset)
    except ValueError as error:
        print(f"분석할 수 없습니다: {error}")
        return

    print_performance(dataset)
    print_summary(results)


def main():
    print("=== Mini NPU Simulator ===")
    print("1. 사용자 입력 (3×3)")
    print("2. data.json 분석")
    print("3. 패턴 자동 생성 (보너스)")

    while True:
        choice = input("선택: ").strip()

        if choice == "1":
            run_manual_mode()
            break
        elif choice == "2":
            run_json_mode()
            break
        elif choice == "3":
            run_generator_mode()
            break
        else:
            print("1, 2 또는 3을 입력해 주세요.")


if __name__ == "__main__":
    main()
