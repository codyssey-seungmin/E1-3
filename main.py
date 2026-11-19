import time
import json
from pathlib import Path

def calculate_mac(pattern, filter_data):
    total = 0.0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_data[row][col]

    return total

def compare_scores(score_a, score_b):
    if abs(score_a - score_b) < 1e-9:
        return "UNDECIDED"

    if score_a > score_b:
        return "A"

    return "B"

def read_matrix(name):
    print(f"{name}을 3줄로 입력하세요. 숫자는 공백으로 구분하세요.")
    matrix = []

    for row in range(3):
        while True:
            parts = input(f"{row + 1}번째 줄: ").split()

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

if __name__ == "__main__":
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