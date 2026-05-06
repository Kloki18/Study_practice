"""
ДОМЕННЫЙ СЕРВИС: Метод Анализа Иерархий (МАИ/AHP)

Упрощённая версия:
- Только расчёт весов и проверка согласованности
- Без анализа проблемных сравнений
- Без предложений по исправлению
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum


# ============================================================
# VALUE OBJECTS
# ============================================================

@dataclass(frozen=True)
class Criterion:
    """Критерий (value object)."""
    name: str

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Название критерия не может быть пустым")


@dataclass(frozen=True)
class Comparison:
    """Одно парное сравнение (по шкале Саати)."""
    criterion_a: str
    criterion_b: str
    value: float

    # Шкала Саати
    SAATY_SCALE = {1, 3, 5, 7, 9, 1/3, 1/5, 1/7, 1/9}

    def __post_init__(self):
        if self.criterion_a == self.criterion_b:
            raise ValueError("Нельзя сравнивать критерий с самим собой")
        is_valid = any(abs(self.value - v) < 0.01 for v in self.SAATY_SCALE)
        if not is_valid:
            raise ValueError(f"Значение {self.value} не соответствует шкале Саати")


@dataclass(frozen=True)
class ComparisonMatrix:
    """Матрица парных сравнений n×n."""
    criteria: List[str]
    values: List[List[float]]  # n×n

    def __post_init__(self):
        n = len(self.criteria)
        if len(self.values) != n:
            raise ValueError("Число строк матрицы должно совпадать с числом критериев")
        for i, row in enumerate(self.values):
            if len(row) != n:
                raise ValueError(f"Строка {i}: ожидалось {n} элементов")
            if abs(self.values[i][i] - 1.0) > 0.001:
                raise ValueError(f"Диагональ [{i}][{i}] должна быть = 1")
        # Проверка обратной симметрии
        for i in range(n):
            for j in range(n):
                if i != j:
                    expected = 1.0 / self.values[i][j] if self.values[i][j] != 0 else float('inf')
                    if abs(self.values[j][i] - expected) > 0.01:
                        raise ValueError(
                            f"Нарушена симметрия: [{i}][{j}]={self.values[i][j]}, [{j}][{i}]={self.values[j][i]}"
                        )

    @property
    def size(self) -> int:
        return len(self.criteria)

    def to_list(self) -> List[List[float]]:
        return [row[:] for row in self.values]


@dataclass(frozen=True)
class WeightsResult:
    """Результат расчёта весов."""
    weights: List[float]  # weights[i] — вес i-го критерия
    lambda_max: float
    ci: float  # Consistency Index
    cr: float  # Consistency Ratio

    # Случайный индекс (RI) для разных размерностей
    RI: Dict[int, float] = field(default_factory=lambda: {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
    })

    def __post_init__(self):
        total = sum(self.weights)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Сумма весов должна быть 1.0, получено {total}")

    @property
    def is_consistent(self) -> bool:
        """Матрица согласована, если CR < 0.1"""
        return self.cr < 0.1

    @property
    def n(self) -> int:
        return len(self.weights)

    def to_dict(self, criteria_names: List[str]) -> Dict[str, float]:
        """Экспорт в словарь {критерий: вес}."""
        return {name: self.weights[i] for i, name in enumerate(criteria_names)}


# ============================================================
# ИНТЕРФЕЙС (ПОРТ)
# ============================================================

class AHPCalculator(ABC):
    """Абстрактный вычислитель МАИ."""

    @abstractmethod
    def calculate(self, matrix: ComparisonMatrix) -> WeightsResult:
        """Вычислить веса и показатели согласованности."""
        raise NotImplementedError


# ============================================================
# ДОМЕННЫЙ СЕРВИС
# ============================================================

class AHPService:
    """Доменный сервис для работы с МАИ."""

    def __init__(self, calculator: AHPCalculator):
        self._calculator = calculator

    def build_matrix(
        self,
        criteria: List[str],
        comparisons: List[Comparison]
    ) -> ComparisonMatrix:
        """Построить матрицу из списка сравнений."""
        n = len(criteria)
        name_to_idx = {name: i for i, name in enumerate(criteria)}

        # Инициализация: все единицы
        matrix = [[1.0] * n for _ in range(n)]

        for comp in comparisons:
            i = name_to_idx[comp.criterion_a]
            j = name_to_idx[comp.criterion_b]
            matrix[i][j] = comp.value
            matrix[j][i] = 1.0 / comp.value

        return ComparisonMatrix(criteria, matrix)

    def calculate_weights(self, matrix: ComparisonMatrix) -> WeightsResult:
        """Вычислить веса."""
        return self._calculator.calculate(matrix)

    # ============ СТАНДАРТНЫЕ НАБОРЫ ============

    @staticmethod
    def default_criteria() -> List[str]:
        return ["возраст", "город", "образование", "доход", "внешность", "интересы", "религия"]

    @staticmethod
    def default_weights() -> Dict[str, float]:
        criteria = AHPService.default_criteria()
        w = 1.0 / len(criteria)
        return {c: w for c in criteria}