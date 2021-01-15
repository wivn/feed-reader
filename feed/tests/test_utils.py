import unittest
from ..utils import schemeify_url
class UtilsTest(unittest.TestCase):
    def test_handles_urls_without_scheme(self):
        url = "example.org"
        correct_url = "http://example.org"
        self.assertEqual(schemeify_url(url), correct_url)
    
    def test_handles_urls_without_scheme_with_subdomain(self):
        url = "www.example.org"
        correct_url = "http://www.example.org"
        self.assertEqual(schemeify_url(url), correct_url)


