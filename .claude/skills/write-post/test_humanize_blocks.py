"""python3 .claude/skills/write-post/test_humanize_blocks.py"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from humanize_blocks import compare  # noqa: E402


class CompareTest(unittest.TestCase):
    def test_unchanged_text_passes(self):
        text = "최소 5개, 최대 5개입니다. `retry`를 두 번 부르면 `retry`가 겹칩니다."
        self.assertEqual(compare(text, text), [])

    def test_dropping_one_repeated_number_is_rejected(self):
        before = "최소 5개, 최대 5개입니다."
        after = "최소와 최대 모두 5개입니다."
        issues = compare(before, after)
        self.assertTrue(any("숫자" in issue for issue in issues), issues)

    def test_dropping_one_repeated_inline_code_is_rejected(self):
        before = "`retry`를 두 번 부르면 `retry`가 겹칩니다."
        after = "`retry`를 두 번 부르면 겹칩니다."
        issues = compare(before, after)
        self.assertTrue(any("인라인 코드" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
