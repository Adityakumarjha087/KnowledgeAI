from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.rag import reranker as reranker_module
from app.rag.reranker import CohereReranker, MockReranker, get_reranker


def _candidate(text, similarity=0.0, rrf_score=0.0):
    return {
        "chunk": SimpleNamespace(text=text),
        "similarity": similarity,
        "rrf_score": rrf_score,
    }


def test_mock_reranker_orders_by_combined_score_and_limits_results():
    candidates = [
        _candidate("low", similarity=0.1, rrf_score=0.1),
        _candidate("high", similarity=0.6, rrf_score=0.3),
        _candidate("mid", similarity=0.4, rrf_score=0.1),
    ]

    result = MockReranker().rerank("query", candidates, top_k=2)

    assert [c["chunk"].text for c in result] == ["high", "mid"]


def test_mock_reranker_treats_missing_scores_as_zero():
    candidates = [{"chunk": SimpleNamespace(text="no scores")}, _candidate("scored", 0.5)]

    result = MockReranker().rerank("query", candidates, top_k=5)

    assert result[0]["chunk"].text == "scored"
    assert len(result) == 2


def test_cohere_reranker_falls_back_to_mock_without_a_real_key():
    candidates = [_candidate("a", 0.2), _candidate("b", 0.9)]

    with patch.object(reranker_module.settings, "RERANK_API_KEY", "your_cohere_key"):
        result = CohereReranker().rerank("query", candidates, top_k=1)

    assert [c["chunk"].text for c in result] == ["b"]


def test_cohere_reranker_remaps_results_to_original_candidates():
    candidates = [_candidate("first"), _candidate("second"), _candidate("third")]
    response = MagicMock()
    response.json.return_value = {
        "results": [
            {"index": 2, "relevance_score": 0.92},
            {"index": 0, "relevance_score": 0.41},
        ]
    }

    with patch.object(reranker_module.settings, "RERANK_API_KEY", "real-key"), patch(
        "app.rag.reranker.httpx.Client"
    ) as client_cls:
        client_cls.return_value.__enter__.return_value.post.return_value = response
        result = CohereReranker().rerank("query", candidates, top_k=2)

    assert [c["chunk"].text for c in result] == ["third", "first"]
    assert result[0]["rerank_score"] == 0.92


def test_cohere_reranker_falls_back_when_the_request_fails():
    candidates = [_candidate("a", 0.2), _candidate("b", 0.9)]

    with patch.object(reranker_module.settings, "RERANK_API_KEY", "real-key"), patch(
        "app.rag.reranker.httpx.Client", side_effect=RuntimeError("network down")
    ):
        result = CohereReranker().rerank("query", candidates, top_k=1)

    assert [c["chunk"].text for c in result] == ["b"]


def test_get_reranker_follows_the_configured_provider():
    with patch.object(reranker_module.settings, "RERANK_PROVIDER", "cohere"):
        assert isinstance(get_reranker(), CohereReranker)
    with patch.object(reranker_module.settings, "RERANK_PROVIDER", "mock"):
        assert isinstance(get_reranker(), MockReranker)
