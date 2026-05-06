"""
ИНФРАСТРУКТУРА: Вычислитель МАИ через numpy (упрощённый)
"""

import numpy as np
from typing import List

from domain.services.ahp_services import (
    AHPCalculator,
    ComparisonMatrix,
    WeightsResult,
)


class NumpyAHPCalculator(AHPCalculator):
    """Реализация через numpy."""

    def calculate(self, matrix: ComparisonMatrix) -> WeightsResult:
        n = matrix.size
        m = np.array(matrix.to_list(), dtype=float)

        # Геометрическое среднее по строкам → веса
        gm = np.exp(np.mean(np.log(m + 1e-10), axis=1))
        weights = gm / np.sum(gm)

        # λ_max через среднее взвешенных сумм
        weighted_sum = m @ weights
        lambda_max = float(np.mean(weighted_sum / (weights + 1e-10)))

        # CI и CR
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = WeightsResult.RI.get(n, 1.49)
        cr = ci / ri if ri > 0 else 0.0

        return WeightsResult(
            weights=weights.tolist(),
            lambda_max=lambda_max,
            ci=float(ci),
            cr=float(cr),
        )