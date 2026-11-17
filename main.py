def calculate_mac(pattern, filter_data):
    total = 0.0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_data[row][col]

    return total


if __name__ == "__main__":
    cross = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    x_shape = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]

    print("십자가 필터 점수:", calculate_mac(cross, cross))
    print("X 필터 점수:", calculate_mac(cross, x_shape))