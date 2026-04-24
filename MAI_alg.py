"""
Метод анализа иерархий (МАИ) для расчета весов критериев.
Автор: Участник 3
"""

import numpy as np
from typing import List, Dict, Any, Tuple


def calculate_ahp_weights(matrix: List[List[float]]) -> Dict[str, Any]:
    """
    Вычисляет веса критериев методом анализа иерархий.

    Аргументы:
        matrix: квадратная матрица парных сравнений (список списков)
                Например, для 3 критериев:
                [[1, 3, 5],
                 [1/3, 1, 2],
                 [1/5, 1/2, 1]]

    Возвращает:
        dict с полями:
        - weights: список весов (сумма = 1)
        - lambda_max: максимальное собственное число
        - ci: индекс согласованности
        - cr: отношение согласованности
        - is_consistent: True если CR < 0.1
    """

    n = len(matrix)
    matrix_np = np.array(matrix, dtype=float)

    # Шаг 1: Вычисление весов методом геометрического среднего
    # Перемножаем элементы в каждой строке и извлекаем корень n-й степени
    geometric_mean = np.exp(np.mean(np.log(matrix_np + 1e-10), axis=1))
    weights = geometric_mean / np.sum(geometric_mean)

    # Шаг 2: Вычисление лямбда-макс (максимального собственного числа)
    weighted_sum = matrix_np @ weights
    lambda_max = np.mean(weighted_sum / (weights + 1e-10))

    # Шаг 3: Индекс согласованности (Consistency Index)
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0

    # Шаг 4: Отношение согласованности (Consistency Ratio)
    # Случайный индекс для матриц разного размера (RI - Random Index)
    ri_values = {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
    }
    ri = ri_values.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    return {
        "weights": weights.tolist(),
        "lambda_max": float(lambda_max),
        "ci": float(ci),
        "cr": float(cr),
        "is_consistent": cr < 0.1
    }


def build_matrix_from_comparisons(
        criteria_names: List[str],
        comparisons: List[Dict[str, Any]]
) -> Tuple[List[List[float]], List[Tuple[str, str]]]:
    """
    Превращает ответы пользователя в матрицу парных сравнений.

    Аргументы:
        criteria_names: список названий критериев, например ["доброта", "доход", "внешность"]
        comparisons: список сравнений, каждое сравнение - словарь вида:
                     {"criterion_a": "доброта", "criterion_b": "доход", "value": 3}
                     value = 1 (равны), 3 (A важнее B в 3 раза), 1/3 (B важнее A)

    Возвращает:
        matrix: квадратная матрица сравнений
        missing_pairs: список пар, для которых не было сравнений (если есть)
    """

    n = len(criteria_names)
    index_map = {name: i for i, name in enumerate(criteria_names)}

    # Инициализируем матрицу единицами на диагонали
    matrix = [[1.0] * n for _ in range(n)]

    recorded_pairs = set()

    for comp in comparisons:
        a = comp["criterion_a"]
        b = comp["criterion_b"]
        value = float(comp["value"])

        i = index_map[a]
        j = index_map[b]

        matrix[i][j] = value
        matrix[j][i] = 1.0 / value

        recorded_pairs.add((min(i, j), max(i, j)))

    # Проверяем, какие пары пропущены
    all_pairs = set((i, j) for i in range(n) for j in range(i + 1, n))
    missing_pairs = []

    for i, j in all_pairs:
        if (i, j) not in recorded_pairs:
            missing_pairs.append((criteria_names[i], criteria_names[j]))
            # Заполняем пропущенные единицами (равная важность)
            matrix[i][j] = 1.0
            matrix[j][i] = 1.0

    return matrix, missing_pairs


def suggest_improvements(matrix: List[List[float]], criteria_names: List[str]) -> List[Dict[str, Any]]:
    """
    Анализирует матрицу и предлагает, какие сравнения исправить для улучшения согласованности.

    Возвращает список проблемных пар с предложениями.
    """

    n = len(matrix)
    result = calculate_ahp_weights(matrix)

    if result["is_consistent"]:
        return []

    matrix_np = np.array(matrix)
    weights = np.array(result["weights"])

    # Вычисляем ожидаемые значения на основе весов
    expected_matrix = np.outer(weights, 1 / weights)

    problems = []
    for i in range(n):
        for j in range(i + 1, n):
            actual = matrix_np[i][j]
            expected = expected_matrix[i][j]
            ratio = actual / expected if expected > 0 else 1

            # Если отклонение больше чем в 2 раза
            if ratio > 2 or ratio < 0.5:
                problems.append({
                    "criterion_a": criteria_names[i],
                    "criterion_b": criteria_names[j],
                    "current_value": float(actual),
                    "suggested_value": round(expected, 2),
                    "deviation": float(ratio)
                })

    return problems


# Пример для самостоятельного тестирования
if __name__ == "__main__":
    # Тест на идеально согласованной матрице
    perfect_matrix = [
        [1, 3, 5],
        [1 / 3, 1, 2],
        [1 / 5, 1 / 2, 1]
    ]

    result = calculate_ahp_weights(perfect_matrix)
    print("=== Тест МАИ ===")
    print(f"Веса: {result['weights']}")
    print(f"CR: {result['cr']:.4f}")
    print(f"Согласовано: {result['is_consistent']}")
    print()

    # Тест на преобразовании сравнений
    criteria = ["доброта", "доход", "внешность"]
    comparisons = [
        {"criterion_a": "доброта", "criterion_b": "доход", "value": 3},
        {"criterion_a": "доброта", "criterion_b": "внешность", "value": 5},
        {"criterion_a": "доход", "criterion_b": "внешность", "value": 2},
    ]

    matrix, missing = build_matrix_from_comparisons(criteria, comparisons)
    print("=== Преобразование сравнений в матрицу ===")
    print("Матрица:")
    for row in matrix:
        print([round(x, 2) for x in row])
    print(f"Пропущенных пар: {missing}")