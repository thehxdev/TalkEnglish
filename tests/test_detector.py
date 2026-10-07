import unittest
from talkenglish.detector import is_english_prompt

class TestDetector(unittest.TestCase):
    def test_pure_english(self):
        self.assertTrue(is_english_prompt("Fix race condition in thread pool worker"))

    def test_english_with_code_and_paths(self):
        self.assertTrue(is_english_prompt("Refactor `auth_handler` in /var/www/api.py to use `user_id`"))

    def test_persian_prompt(self):
        self.assertFalse(is_english_prompt("تابع `process_data` در مسیر /app/utils.py را بازنویسی کن"))

    def test_chinese_prompt(self):
        self.assertFalse(is_english_prompt("重构 user_service 中的 authenticate 方法"))

    def test_code_only_prompt(self):
        self.assertTrue(is_english_prompt("```python\ndef test(): pass\n```"))

if __name__ == "__main__":
    unittest.main()
