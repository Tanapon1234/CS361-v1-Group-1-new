from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.v2.models.submission import EvaluationRound


class EvaluationRoundDAO(ABC):
    @abstractmethod
    def get_by_id(self, round_id: int) -> EvaluationRound | None: ...

    @abstractmethod
    def find_page(
        self, *, is_open: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[EvaluationRound], int]:
        """Newest period first."""

    @abstractmethod
    def has_submissions(self, round_id: int) -> bool: ...

    @abstractmethod
    def add(self, evaluation_round: EvaluationRound) -> EvaluationRound: ...

    @abstractmethod
    def update(
        self, evaluation_round: EvaluationRound, values: Mapping[str, Any]
    ) -> EvaluationRound: ...
