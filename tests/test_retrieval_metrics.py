from app.evaluation.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank


def test_metrics():
    retrieved = ["a", "b", "c"]
    relevant = ["b", "d"]

    assert precision_at_k(retrieved, relevant, 2) == 0.5
    assert recall_at_k(retrieved, relevant, 3) == 0.5
    assert reciprocal_rank(retrieved, relevant) == 0.5
