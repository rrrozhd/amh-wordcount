import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from wc import count

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


if __name__ == "__main__":
    unittest.main()
