from __future__ import annotations

from typing import Dict, List

from app.evaluation.answer_metrics import normalized_token_f1
from app.evaluation.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank


class Evaluator:
    def evaluate_retrieval(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 10,
    ) -> Dict[str, float]:
        return {
            f"precision@{k}": precision_at_k(retrieved_ids, relevant_ids, k),
            f"recall@{k}": recall_at_k(retrieved_ids, relevant_ids, k),
            "mrr": reciprocal_rank(retrieved_ids, relevant_ids),
        }

    def evaluate_answer(self, prediction: str, reference: str) -> Dict[str, float]:
        return {"token_f1": normalized_token_f1(prediction, reference)}
