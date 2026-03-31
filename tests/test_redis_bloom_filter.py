import unittest

from redis_bloom_filter import RedisBloomDetailFilter, normalize_urls


class FakeRedisClient:
    def __init__(self, exists_reply=None):
        self.commands = []
        self.exists_reply = exists_reply or []

    def execute_command(self, *args):
        self.commands.append(args)
        cmd = args[0]
        if cmd == "BF.RESERVE":
            return "OK"
        if cmd == "BF.MEXISTS":
            return self.exists_reply
        if cmd == "BF.MADD":
            return [1 for _ in args[2:]]
        raise RuntimeError(f"unexpected command: {cmd}")


class RedisBloomDetailFilterTests(unittest.TestCase):
    def test_normalize_urls_removes_duplicate_and_blank(self):
        self.assertEqual(
            normalize_urls(
                ["", "https://a.com", "https://a.com", "  ", "https://b.com"]
            ),
            ["https://a.com", "https://b.com"],
        )

    def test_filter_new_urls_checks_bloom_and_only_returns_unknown(self):
        client = FakeRedisClient(exists_reply=[1, 0, 1])
        bloom = RedisBloomDetailFilter(
            client=client,
            key="crawler:detail:test",
            error_rate=0.001,
            capacity=10000,
        )

        urls = ["https://a.com/1", "https://a.com/2", "https://a.com/3"]
        new_urls = bloom.filter_new_urls(urls)

        self.assertEqual(new_urls, ["https://a.com/2"])
        self.assertEqual(client.commands[0][0], "BF.RESERVE")
        self.assertEqual(client.commands[1][0], "BF.MEXISTS")

    def test_mark_crawled_adds_all_urls_to_bloom(self):
        client = FakeRedisClient(exists_reply=[0, 0])
        bloom = RedisBloomDetailFilter(
            client=client,
            key="crawler:detail:test",
            error_rate=0.001,
            capacity=10000,
        )

        urls = ["https://a.com/1", "https://a.com/2"]
        bloom.mark_crawled(urls)

        self.assertEqual(client.commands[0][0], "BF.RESERVE")
        self.assertEqual(client.commands[1][0], "BF.MADD")
        self.assertEqual(len(client.commands[1]), 4)


if __name__ == "__main__":
    unittest.main()
