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