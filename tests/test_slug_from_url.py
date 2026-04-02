import re
import unittest

from prefect_tasks import slug_from_url


class SlugFromUrlTests(unittest.TestCase):
    def test_uses_full_url_hash_for_query_urls(self):
        url_a = "http://www.cnfood.net/exhibit/show.php?itemid=2873"
        url_b = "http://www.cnfood.net/exhibit/show.php?itemid=9999"

        slug_a = slug_from_url(url_a)
        slug_b = slug_from_url(url_b)

        self.assertNotEqual(slug_a, slug_b)
        self.assertRegex(slug_a, r"^[a-f0-9]{32}$")
        self.assertRegex(slug_b, r"^[a-f0-9]{32}$")


if __name__ == "__main__":
    unittest.main()
