"""
Алгоритм оценки совместимости между двумя пользователями.
Автор: Участник 3
"""

from typing import Dict, List, Any, Union
import numpy as np


def compute_similarity_numeric(value_a: float, value_b: float, min_val: float = 1, max_val: float = 10) -> float:
    """
    Вычисляет сходство для числовых критериев (возраст, доход, оценка качеств).

    Формула: 1 - (нормированная разница)
    """
    if value_a is None or value_b is None:
        return 0.0

    diff = abs(value_a - value_b)
    normalized_diff = diff / (max_val - min_val)
    similarity = max(0.0, min(1.0, 1 - normalized_diff))
    return similarity


def compute_similarity_categorical(value_a: Any, value_b: Any) -> float:
    """
    Вычисляет сходство для категориальных критериев (пол, город, вероисповедание).
    """
    if value_a is None or value_b is None:
        return 0.0
    return 1.0 if value_a == value_b else 0.0


def compute_similarity_multiset(list_a: List[Any], list_b: List[Any]) -> float:
    """
    Вычисляет сходство для множественных критериев (интересы, ценности, хобби).
    Используется коэффициент Жаккара: |A ∩ B| / |A ∪ B|
    """
    if not list_a or not list_b:
        return 0.0

    set_a = set(list_a) if isinstance(list_a, list) else {list_a}
    set_b = set(list_b) if isinstance(list_b, list) else {list_b}

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0

    return intersection / union


def compute_compatibility(
        profile_a: Dict[str, Any],
        profile_b: Dict[str, Any],
        criteria_weights: Dict[str, float]
) -> Dict[str, Any]:
    """
    Вычисляет совместимость между пользователем A и кандидатом B.

    Аргументы:
        profile_a: профиль пользователя A (его качества и предпочтения)
        profile_b: профиль кандидата B
        criteria_weights: веса критериев от пользователя A

    Возвращает:
        dict с полями:
        - compatibility_score: итоговый балл (0-100)
        - breakdown: список с детализацией по каждому критерию
        - summary: краткая сводка (лучшие и худшие критерии)
    """

    total_score = 0.0
    breakdown = []

    for criterion, weight in criteria_weights.items():
        # Получаем значения из профилей
        value_a = profile_a.get(criterion)
        value_b = profile_b.get(criterion)

        if value_a is None or value_b is None:
            similarity = 0.0
            criterion_type = "unknown"
        else:
            # Определяем тип критерия и выбираем функцию сходства
            if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
                # Числовой критерий (возраст, доход, уровень образования)
                similarity = compute_similarity_numeric(value_a, value_b)
                criterion_type = "numeric"
            elif isinstance(value_a, list) or isinstance(value_b, list):
                # Множественный критерий (интересы, ценности)
                similarity = compute_similarity_multiset(value_a, value_b)
                criterion_type = "multiset"
            else:
                # Категориальный критерий (пол, город)
                similarity = compute_similarity_categorical(value_a, value_b)
                criterion_type = "categorical"

        contribution = weight * similarity
        total_score += contribution

        breakdown.append({
            "criterion": criterion,
            "criterion_type": criterion_type,
            "weight": round(weight, 4),
            "similarity": round(similarity, 4),
            "contribution": round(contribution, 4),
            "contribution_percent": round(contribution * 100, 2),
            "value_a": value_a,
            "value_b": value_b
        })

    # Итоговый балл от 0 до 100
    final_score = round(total_score * 100, 2)

    # Находим лучший и худший критерии
    breakdown_sorted = sorted(breakdown, key=lambda x: x["similarity"], reverse=True)

    summary = {
        "best_criterion": breakdown_sorted[0]["criterion"] if breakdown_sorted else None,
        "best_similarity": breakdown_sorted[0]["similarity"] if breakdown_sorted else 0,
        "worst_criterion": breakdown_sorted[-1]["criterion"] if breakdown_sorted else None,
        "worst_similarity": breakdown_sorted[-1]["similarity"] if breakdown_sorted else 0,
        "average_similarity": round(np.mean([b["similarity"] for b in breakdown]), 4) if breakdown else 0
    }

    return {
        "compatibility_score": final_score,
        "breakdown": breakdown,
        "summary": summary
    }


def compute_batch_compatibility(
        user_profile: Dict[str, Any],
        candidates_profiles: List[Dict[str, Any]],
        criteria_weights: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Вычисляет совместимость пользователя с множеством кандидатов.
    Используется для массового расчета и оптимизации.

    Возвращает список кандидатов с их баллами совместимости, отсортированный по убыванию.
    """

    results = []

    for candidate in candidates_profiles:
        compat_result = compute_compatibility(user_profile, candidate, criteria_weights)
        results.append({
            "candidate_id": candidate.get("user_id"),
            "candidate_name": candidate.get("name"),
            "compatibility_score": compat_result["compatibility_score"],
            "summary": compat_result["summary"],
            "breakdown": compat_result["breakdown"]
        })

    # Сортировка по убыванию совместимости
    results.sort(key=lambda x: x["compatibility_score"], reverse=True)

    return results


# Пример для самостоятельного тестирования
if __name__ == "__main__":
    # Тестовые профили
    profile_user = {
        "user_id": 1,
        "name": "Анна",
        "доброта": 8,
        "доход": 5,
        "внешность": 7,
        "интересы": ["спорт", "путешествия", "чтение"],
        "город": "Москва"
    }

    profile_candidate = {
        "user_id": 2,
        "name": "Иван",
        "доброта": 9,
        "доход": 6,
        "внешность": 6,
        "интересы": ["спорт", "кино", "путешествия"],
        "город": "Москва"
    }

    # Веса критериев (от пользователя)
    weights = {
        "доброта": 0.5,
        "доход": 0.2,
        "внешность": 0.15,
        "интересы": 0.1,
        "город": 0.05
    }

    result = compute_compatibility(profile_user, profile_candidate, weights)

    print("=== Тест совместимости ===")
    print(f"Совместимость: {result['compatibility_score']}%")
    print(
        f"\nЛучший критерий: {result['summary']['best_criterion']} ({result['summary']['best_similarity'] * 100:.0f}%)")
    print(
        f"Худший критерий: {result['summary']['worst_criterion']} ({result['summary']['worst_similarity'] * 100:.0f}%)")
    print("\nДетализация:")
    for item in result["breakdown"]:
        print(
            f"  {item['criterion']}: сходство {item['similarity'] * 100:.0f}% → вклад {item['contribution_percent']:.1f} баллов")
