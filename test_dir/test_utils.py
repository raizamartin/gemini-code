import unittest
from src.gemini_cli.utils import count_tokens

class TestCountTokens(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(count_tokens(""), 0)

    def test_short_string(self):
        text = "This is a short string."
        tokens = count_tokens(text)
        self.assertTrue(5 <= tokens <= 10, f"Token count out of range: {tokens}")

    def test_long_string(self):
        text = "This is a much longer string with more words to test the token counting function. It should return a higher number of tokens."
        tokens = count_tokens(text)
        self.assertTrue(20 <= tokens <= 30, f"Token count out of range: {tokens}")

    def test_special_characters(self):
        text = "String with !@#$%^&*()_+ special characters."
        tokens = count_tokens(text)
        self.assertTrue(7 <= tokens <= 15, f"Token count out of range: {tokens}")

if __name__ == '__main__':
    unittest.main()
