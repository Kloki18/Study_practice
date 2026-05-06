"""
ДОМЕННЫЙ СЕРВИС: Оценка совместимости

Содержит ТОЛЬКО бизнес-логику:
- Какие типы сходства бывают (числовое, категориальное, множественное)
- Как агрегировать сходства по критериям с учётом весов
- Что считать "хорошей" совместимостью

НЕ содержит:
- Конкретных формул расчёта similarity (это infrastructure)
- SQL-запросов
- HTTP-логики
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


# ============================================================
# ТИПЫ КРИТЕРИЕВ
# ============================================================

class CriterionType(Enum):
    """
    Тип критерия определяет, как вычислять сходство.

    Это БИЗНЕС-КЛАССИФИКАЦИЯ: она диктует правила,
    а не технические детали.
    """
    NUMERIC = "numeric"  # возраст, доход, внешность (шкала 1-10)
    CATEGORICAL = "categorical"  # пол, город, образование, религия (точное совпадение)
    MULTISET = "multiset"  # интересы, хобби (пересечение множеств)
    UNKNOWN = "unknown"  # fallback для отсутствующих данных


# ============================================================
# VALUE OBJECTS
# ============================================================

@dataclass(frozen=True)
class CriterionValue:
    """
    Значение критерия из профиля пользователя.

    Может быть:
    - числом (возраст=25, доход=7)
    - строкой (город="Москва", образование="высшее")
    - списком (интересы=["спорт", "книги"])
    - None (данные отсутствуют)
    """
    raw_value: Any

    @property
    def is_empty(self) -> bool:
        """Значение отсутствует или пустое."""
        if self.raw_value is None:
            return True
        if isinstance(self.raw_value, list) and len(self.raw_value) == 0:
            return True
        if isinstance(self.raw_value, str) and not self.raw_value.strip():
            return True
        return False

    def infer_type(self) -> CriterionType:
        """
        Автоматически определяет тип критерия по значению.

        Бизнес-правила классификации:
        - int/float → NUMERIC
        - list → MULTISET
        - str (и все остальные) → CATEGORICAL
        - None → UNKNOWN
        """
        if self.is_empty:
            return CriterionType.UNKNOWN
        if isinstance(self.raw_value, (int, float)):
            return CriterionType.NUMERIC
        if isinstance(self.raw_value, list):
            return CriterionType.MULTISET
        return CriterionType.CATEGORICAL


@dataclass(frozen=True)
class SimilarityScore:
    """
    Результат сравнения двух значений по одному критерию.

    Всегда в диапазоне [0.0, 1.0]:
    - 1.0 = полное совпадение
    - 0.0 = полное несовпадение
    """
    value: float

    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"Сходство должно быть в диапазоне [0, 1], получено {self.value}"
            )

    @property
    def as_percent(self) -> float:
        """Сходство в процентах (0-100)."""
        return round(self.value * 100, 2)

    def __mul__(self, weight: float) -> float:
        """Умножение на вес (для агрегации)."""
        return self.value * weight

    def __lt__(self, other: 'SimilarityScore') -> bool:
        return self.value < other.value

    def __gt__(self, other: 'SimilarityScore') -> bool:
        return self.value > other.value


@dataclass(frozen=True)
class CriterionContribution:
    """
    Вклад одного критерия в итоговую совместимость.

    Содержит:
    - название критерия
    - его тип (как вычисляли сходство)
    - вес (из МАИ)
    - сходство (0-1)
    - вклад = вес × сходство
    - исходные значения (для отладки/объяснения)
    """
    criterion_name: str
    criterion_type: CriterionType
    weight: float
    similarity: SimilarityScore
    value_a: Optional[Any] = None
    value_b: Optional[Any] = None

    @property
    def contribution(self) -> float:
        """Итоговый вклад этого критерия (вес × сходство)."""
        return round(self.weight * self.similarity.value, 4)

    @property
    def contribution_percent(self) -> float:
        """Вклад в процентах от итогового балла."""
        return round(self.contribution * 100, 2)


@dataclass(frozen=True)
class CompatibilityBreakdown:
    """
    Полная детализация совместимости по всем критериям.
    """
    items: List[CriterionContribution]

    @property
    def best_criterion(self) -> Optional[CriterionContribution]:
        """Критерий с наилучшим сходством."""
        if not self.items:
            return None
        return max(self.items, key=lambda x: x.similarity.value)

    @property
    def worst_criterion(self) -> Optional[CriterionContribution]:
        """Критерий с наихудшим сходством."""
        if not self.items:
            return None
        return min(self.items, key=lambda x: x.similarity.value)

    @property
    def average_similarity(self) -> float:
        """Среднее сходство по всем критериям."""
        if not self.items:
            return 0.0
        return sum(item.similarity.value for item in self.items) / len(self.items)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Экспорт для presentation/application слоёв.
        """
        return [
            {
                "criterion": item.criterion_name,
                "criterion_type": item.criterion_type.value,
                "weight": item.weight,
                "similarity": item.similarity.value,
                "contribution": item.contribution,
                "contribution_percent": item.contribution_percent,
                "value_a": item.value_a,
                "value_b": item.value_b,
            }
            for item in self.items
        ]


@dataclass(frozen=True)
class CompatibilityResult:
    """
    Итоговый результат совместимости двух профилей.

    Бизнес-правила:
    - Итоговый балл: 0-100 (проценты)
    - Детализация по каждому критерию
    - Определение лучших/худших критериев
    """
    score: float  # 0-100
    breakdown: CompatibilityBreakdown

    def __post_init__(self):
        if not (0.0 <= self.score <= 100.0):
            raise ValueError(
                f"Балл совместимости должен быть в диапазоне [0, 100], получено {self.score}"
            )

    @property
    def score_normalized(self) -> float:
        """Балл в диапазоне [0, 1]."""
        return self.score / 100.0

    @property
    def is_good_match(self) -> bool:
        """
        Бизнес-правило: хорошая совместимость > 70%.
        Этот порог можно менять в зависимости от бизнес-требований.
        """
        return self.score >= 70.0

    @property
    def is_excellent_match(self) -> bool:
        """Отличная совместимость > 85%."""
        return self.score >= 85.0

    def summary_dict(self) -> Dict[str, Any]:
        """
        Краткая сводка для отображения (без полной детализации).
        """
        return {
            "compatibility_score": self.score,
            "best_criterion": self.breakdown.best_criterion.criterion_name if self.breakdown.best_criterion else None,
            "best_similarity": self.breakdown.best_criterion.similarity.as_percent if self.breakdown.best_criterion else 0,
            "worst_criterion": self.breakdown.worst_criterion.criterion_name if self.breakdown.worst_criterion else None,
            "worst_similarity": self.breakdown.worst_criterion.similarity.as_percent if self.breakdown.worst_criterion else 0,
            "average_similarity": round(self.breakdown.average_similarity * 100, 2),
        }


# ============================================================
# ИНТЕРФЕЙСЫ (ПОРТЫ) ДЛЯ ВЫЧИСЛИТЕЛЕЙ
# ============================================================

class SimilarityFunction(ABC):
    """
    Абстрактная функция сходства для одного типа критериев.

    Infrastructure реализует конкретные алгоритмы:
    - numeric_similarity (через нормализацию разницы)
    - categorical_similarity (точное совпадение)
    - multiset_similarity (коэффициент Жаккара)
    """

    @abstractmethod
    def compute(self, value_a: Any, value_b: Any) -> SimilarityScore:
        """
        Вычислить сходство двух значений.

        Args:
            value_a, value_b: значения критерия из двух профилей

        Returns:
            SimilarityScore в диапазоне [0, 1]
        """
        raise NotImplementedError


class ProfileReader(ABC):
    """
    Абстрактный интерфейс для чтения профиля.

    Domain говорит: "Дай мне значение критерия X для пользователя Y".
    Infrastructure реализует: лезет в БД, кэш, внешний API.
    """

    @abstractmethod
    def get_criterion_value(self, user_id: int, criterion_name: str) -> Any:
        """Получить значение критерия для пользователя."""
        raise NotImplementedError


# ============================================================
# ДОМЕННЫЙ СЕРВИС (ЧИСТАЯ БИЗНЕС-ЛОГИКА)
# ============================================================

class CompatibilityEvaluator:
    """
    Доменный сервис для оценки совместимости.

    Содержит бизнес-логику агрегации:
    - Как объединять сходства по критериям с учётом весов
    - Как определять тип критерия
    - Как нормализовать итоговый балл
    """

    def __init__(self, similarity_functions: Dict[CriterionType, SimilarityFunction]):
        """
        Внедрение зависимости: словарь функций сходства по типам.

        Пример:
        {
            CriterionType.NUMERIC: NumericSimilarityImpl(),
            CriterionType.CATEGORICAL: CategoricalSimilarityImpl(),
            CriterionType.MULTISET: MultisetSimilarityImpl(),
        }
        """
        self._functions = similarity_functions

    def evaluate(
            self,
            profile_a: Dict[str, Any],
            profile_b: Dict[str, Any],
            weights: Dict[str, float]
    ) -> CompatibilityResult:
        """
        Оценить совместимость двух профилей.

        Бизнес-логика:
        1. Для каждого критерия из weights:
           - Получить значения из профилей
           - Определить тип критерия
           - Выбрать функцию сходства
           - Вычислить сходство
           - Посчитать вклад = вес × сходство
        2. Суммировать вклады → итоговый балл (0-100)

        Args:
            profile_a: профиль первого пользователя (словарь)
            profile_b: профиль второго пользователя
            weights: веса критериев (из МАИ), сумма = 1.0

        Returns:
            CompatibilityResult с итоговым баллом и детализацией
        """
        contributions = []
        total_score = 0.0

        for criterion_name, weight in weights.items():
            # Получаем значения
            value_a = profile_a.get(criterion_name)
            value_b = profile_b.get(criterion_name)

            # Определяем тип критерия
            val_a = CriterionValue(value_a)
            val_b = CriterionValue(value_b)

            # Если хотя бы одно значение пустое — сходство 0
            if val_a.is_empty or val_b.is_empty:
                similarity = SimilarityScore(0.0)
                criterion_type = CriterionType.UNKNOWN
            else:
                # Определяем тип (берём непустое значение)
                criterion_type = val_a.infer_type()

                # Выбираем функцию сходства
                func = self._functions.get(criterion_type)
                if func is None:
                    # fallback: если нет функции для этого типа
                    similarity = SimilarityScore(0.0)
                else:
                    similarity = func.compute(value_a, value_b)

            # Создаём запись о вкладе
            contribution = CriterionContribution(
                criterion_name=criterion_name,
                criterion_type=criterion_type,
                weight=weight,
                similarity=similarity,
                value_a=value_a,
                value_b=value_b,
            )

            contributions.append(contribution)
            total_score += contribution.contribution

        # Нормализуем в проценты (веса уже в сумме дают 1.0)
        final_score = round(total_score * 100, 2)

        return CompatibilityResult(
            score=final_score,
            breakdown=CompatibilityBreakdown(items=contributions),
        )

    def evaluate_batch(
            self,
            user_profile: Dict[str, Any],
            candidates: List[Dict[str, Any]],
            weights: Dict[str, float]
    ) -> List[CompatibilityResult]:
        """
        Массовая оценка совместимости с несколькими кандидатами.

        Бизнес-правило: результаты сортируются по убыванию совместимости.
        """
        results = [
            self.evaluate(user_profile, candidate, weights)
            for candidate in candidates
        ]

        # Сортировка по убыванию совместимости
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def get_top_matches(
            self,
            user_profile: Dict[str, Any],
            candidates: List[Dict[str, Any]],
            weights: Dict[str, float],
            limit: int = 20
    ) -> List[CompatibilityResult]:
        """
        Получить топ-N наиболее совместимых кандидатов.

        Бизнес-правило: по умолчанию показываем топ-20,
        но можно запросить больше/меньше.
        """
        all_results = self.evaluate_batch(user_profile, candidates, weights)
        return all_results[:limit]

    def validate_weights(self, weights: Dict[str, float]) -> List[str]:
        """
        Проверить корректность весов перед вычислением совместимости.

        Возвращает список предупреждений.
        """
        warnings = []

        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            warnings.append(
                f"Сумма весов должна быть 1.0, текущая сумма: {total:.3f}"
            )

        for name, weight in weights.items():
            if weight < 0:
                warnings.append(f"Вес критерия '{name}' отрицательный: {weight}")
            if weight > 1:
                warnings.append(f"Вес критерия '{name}' больше 1: {weight}")

        return warnings