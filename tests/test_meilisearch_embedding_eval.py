import unittest

from meilisearch_embedding_eval import evaluate_hit_rank


class MeilisearchEmbeddingEvalTests(unittest.TestCase):
    def test_evaluate_hit_rank_returns_one_based_rank(self):
        hits = [
            {"id": "doc-b"},
            {"id": "doc-a"},
            {"id": "doc-c"},
        ]
        self.assertEqual(evaluate_hit_rank(hits, "doc-a"), 2)

    def test_evaluate_hit_rank_returns_minus_one_when_not_found(self):
        hits = [{"id": "doc-b"}, {"id": "doc-c"}]
        self.assertEqual(evaluate_hit_rank(hits, "doc-a"), -1)


if __name__ == "__main__":
    unittest.main()
