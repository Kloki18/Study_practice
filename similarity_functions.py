"""
ИНФРАСТРУКТУРНЫЙ СЕРВИС: Функции сходства

Реализует интерфейс SimilarityFunction из domain/services/compatibility_service.py
с конкретными алгоритмами вычисления сходства.

Только здесь разрешено:
- Числовые формулы сходства
- Коэффициент Жаккара
- Нормализация значений
"""

from typing import Any, List
import math

from domain.services.compatibility_services import (
    SimilarityFunction,
    SimilarityScore,
)


class NumericSimilarity(SimilarityFunction):
    """
    Сходство для числовых критериев (возраст, доход, внешность).

    Алгоритм: 1 - |a - b| / range
    где range — размах шкалы (по умолчанию 1-10, то есть range=9)

    Пример:
    - a=5, b=8 → similarity = 1 - 3/9 = 0.67
    - a=1, b=10 → similarity = 1 - 9/9 = 0.0
    - a=5, b=5 → similarity = 1.0
    """

    def __init__(self, min_value: float = 1.0, max_value: float = 10.0):
        self._min = min_value
        self._max = max_value
        self._range = max_value - min_value

    def compute(self, value_a: Any, value_b: Any) -> SimilarityScore:
        # Приводим к float
        try:
            a = float(value_a)
            b = float(value_b)
        except (TypeError, ValueError):
            return SimilarityScore(0.0)

        # Нормализованная разница
        diff = abs(a - b)
        normalized_diff = diff / self._range

        # Сходство = 1 - нормализованная разница
        similarity = max(0.0, min(1.0, 1.0 - normalized_diff))

        return SimilarityScore(round(similarity, 4))


class AgeSimilarity(NumericSimilarity):
    """
    Сходство по возрасту с особой логикой.

    Бизнес-правила:
    - Разница в возрасте до 3 лет → почти полное совпадение (>0.9)
    - Разница 3-7 лет → умеренное сходство
    - Разница >15 лет → низкое сходство (<0.2)

    Использует нелинейную шкалу вместо линейной.
    """

    def __init__(self):
        # Возраст: от 18 до 80 лет
        super().__init__(min_value=18.0, max_value=80.0)

    def compute(self, value_a: Any, value_b: Any) -> SimilarityScore:
        try:
            age_a = float(value_a)
            age_b = float(value_b)
        except (TypeError, ValueError):
            return SimilarityScore(0.0)

        diff = abs(age_a - age_b)

        # Нелинейная функция сходства для возраста
        if diff <= 3:
            similarity = 0.95  # почти идеально
        elif diff <= 7:
            similarity = 0.8 - (diff - 3) * 0.05  # 0.8 → 0.6
        elif diff <= 15:
            similarity = 0.6 - (diff - 7) * 0.04  # 0.6 → 0.28
        else:
            similarity = max(0.1, 0.28 - (diff - 15) * 0.02)  # медленно падает

        return SimilarityScore(round(similarity, 4))


class CategoricalSimilarity(SimilarityFunction):
    """
    Сходство для категориальных критериев (город, образование, религия, пол).

    Алгоритм:
    - Точное совпадение → 1.0
    - Разные значения → 0.0

    Нет промежуточных значений, потому что:
    - "Москва" и "Питер" — разные города (0.0), хотя можно было бы добавить
      географическую близость как дополнительный критерий
    """

    def compute(self, value_a: Any, value_b: Any) -> SimilarityScore:
        # Приводим к строкам и сравниваем
        str_a = str(value_a).strip().lower() if value_a is not None else ""
        str_b = str(value_b).strip().lower() if value_b is not None else ""

        if not str_a or not str_b:
            return SimilarityScore(0.0)

        similarity = 1.0 if str_a == str_b else 0.0
        return SimilarityScore(similarity)


class MultisetSimilarity(SimilarityFunction):
    """
    Сходство для множественных критериев (интересы, хобби).

    Алгоритм: коэффициент Жаккара
    J(A, B) = |A ∩ B| / |A ∪ B|

    Пример:
    - A = ["спорт", "книги", "кино"]
    - B = ["спорт", "музыка", "кино"]
    - Пересечение: {"спорт", "кино"} = 2
    - Объединение: {"спорт", "книги", "кино", "музыка"} = 4
    - J = 2/4 = 0.5
    """

    def compute(self, value_a: Any, value_b: Any) -> SimilarityScore:
        # Приводим к множествам
        set_a = self._to_set(value_a)
        set_b = self._to_set(value_b)

        if not set_a or not set_b:
            return SimilarityScore(0.0)

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)

        if union == 0:
            return SimilarityScore(0.0)

        jaccard = intersection / union
        return SimilarityScore(round(jaccard, 4))

    @staticmethod
    def _to_set(value: Any) -> set:
        """Преобразует значение в множество."""
        if value is None:
            return set()
        if isinstance(value, list):
            # Нормализуем: lower, strip для строк
            return {
                item.strip().lower() if isinstance(item, str) else item
                for item in value
            }
        if isinstance(value, (set, tuple)):
            return set(value)
        # Одиночное значение → множество из одного элемента
        return {str(value).strip().lower()}


# ============================================================
# ФАБРИКА ФУНКЦИЙ СХОДСТВА
# ============================================================

def create_default_similarity_functions() -> dict:
    """
    Создаёт стандартный набор функций сходства.

    Возвращает словарь {CriterionType: SimilarityFunction},
    который можно внедрить в CompatibilityEvaluator.
    """
    from domain.services.compatibility_services import CriterionType

    return {
        CriterionType.NUMERIC: NumericSimilarity(),
        CriterionType.CATEGORICAL: CategoricalSimilarity(),
        CriterionType.MULTISET: MultisetSimilarity(),
    }