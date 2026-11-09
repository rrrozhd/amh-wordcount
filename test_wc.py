import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from wc import count, top_words

HERE = os.path.dirname(os.path.abspath(__file__))
WC_PY = os.path.join(HERE, "wc.py")

CASES = {
    "empty": b"",
    "single line": b"hello world\n",
    "no final newline": b"one two\nthree",
    "mixed whitespace": b"  a\tb  \t c\n\n\x0bd\x0c e  \n",
    "crlf": b"first line\r\nsecond\r\n",
    "only whitespace": b" \t \n \n",
}


def run(args, stdin=b""):
    return subprocess.run(
        [sys.executable, WC_PY, *args], input=stdin, capture_output=True
    )


class CountTests(unittest.TestCase):
    def test_counts(self):
        expected = {
            "empty": (0, 0, 0),
            "single line": (1, 2, 12),
            "no final newline": (1, 3, 13),
            "mixed whitespace": (3, 5, 20),
            "crlf": (2, 3, 20),
            "only whitespace": (2, 0, 6),
        }
        for name, data in CASES.items():
            with self.subTest(name):
                self.assertEqual(count(data), expected[name])

    def test_multibyte_characters_are_counted_once(self):
        self.assertEqual(count("héllo wörld\n".encode("utf-8")), (1, 2, 12))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, data):
        path = os.path.join(self.tmp.name, "input.txt")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_file_prints_counts_and_name(self):
        path = self.write(b"one two\nthree four five\n")
        result = run([path])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), f"2 5 24 {path}\n")
        self.assertEqual(result.stderr, b"")

    def test_stdin_prints_three_counts(self):
        result = run([], stdin=b"one two\nthree four five\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), "2 5 24\n")

    def test_empty_stdin(self):
        result = run([], stdin=b"")
        self.assertEqual(result.stdout.decode(), "0 0 0\n")

    def test_missing_file(self):
        path = os.path.join(self.tmp.name, "does-not-exist.txt")
        result = run([path])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(path, result.stderr.decode())

    @unittest.skipIf(shutil.which("wc") is None, "system wc not available")
    def test_matches_system_wc_for_ascii(self):
        for name, data in CASES.items():
            with self.subTest(name):
                path = self.write(data)
                ours = run([path]).stdout.decode().split()
                theirs = subprocess.run(
                    ["wc", "-l", "-w", "-c", path], capture_output=True
                ).stdout.decode().split()
                self.assertEqual(ours, theirs)
                ours_stdin = run([], stdin=data).stdout.decode().split()
                self.assertEqual(ours_stdin, theirs[:3])


class TopWordsTests(unittest.TestCase):
    def test_orders_by_count_then_alphabetically(self):
        data = b"b a c b a b d\n"
        self.assertEqual(top_words(data, 3), [("b", 3), ("a", 2), ("c", 1)])

    def test_case_insensitive(self):
        self.assertEqual(top_words(b"The the THE cat\n", 2), [("the", 3), ("cat", 1)])

    def test_n_larger_than_distinct_words(self):
        self.assertEqual(top_words(b"x y x", 10), [("x", 2), ("y", 1)])

    def test_empty_input(self):
        self.assertEqual(top_words(b"", 3), [])

    def test_utf8_words(self):
        self.assertEqual(top_words("Wörld wörld\n".encode("utf-8"), 1), [("wörld", 2)])


class TopCliTests(unittest.TestCase):
    TEXT = b"the cat and the dog\nThe Dog ran\nzebra apple\n"
    EXPECTED = "3 the\n2 dog\n1 and\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "input.txt")
        with open(self.path, "wb") as f:
            f.write(self.TEXT)

    def test_top_file(self):
        result = run(["--top", "3", self.path])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), self.EXPECTED)
        self.assertEqual(result.stderr, b"")

    def test_top_option_after_file_and_equals_form(self):
        self.assertEqual(run([self.path, "--top=3"]).stdout.decode(), self.EXPECTED)

    def test_top_stdin(self):
        result = run(["--top", "3"], stdin=self.TEXT)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), self.EXPECTED)

    def test_top_missing_file(self):
        missing = os.path.join(self.tmp.name, "nope.txt")
        result = run(["--top", "2", missing])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(missing, result.stderr.decode())

    def test_bad_top_values_are_usage_errors(self):
        for args in (["--top"], ["--top", "0"], ["--top", "-1"], ["--top", "x"],
                     ["--top", "1", "--top", "2"], ["--top", "1", "a", "b"]):
            with self.subTest(args):
                result = run(args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertTrue(result.stderr.startswith(b"usage:"))


class LegacyArgumentTests(unittest.TestCase):
    def test_two_files_keep_original_usage(self):
        result = run(["a", "b"])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr.decode(), "usage: python wc.py [FILE]\n")

    def test_dash_prefixed_filename_is_still_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "-x"), "wb") as f:
                f.write(b"a b\n")
            result = subprocess.run(
                [sys.executable, WC_PY, "-x"], cwd=tmp, capture_output=True
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), "1 2 4 -x\n")


if __name__ == "__main__":
    unittest.main()
