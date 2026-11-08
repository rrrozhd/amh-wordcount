"""Count lines, words and characters, like the Unix wc command.

Usage:
    python wc.py FILE   prints "LINES WORDS CHARS FILE"
    python wc.py        reads standard input and prints "LINES WORDS CHARS"
"""

import sys


def count(data):
    """Return (lines, words, chars) for raw bytes.

    Lines are newline characters, so a final line without a newline adds
    none. Words are runs of non-whitespace, split on ASCII whitespace as wc
    does in the C locale. Characters are decoded UTF-8 characters; carriage
    returns are kept, so CRLF counts as two characters.
    """
    lines = data.count(b"\n")
    words = len(data.split())
    chars = len(data.decode("utf-8", errors="replace"))
    return lines, words, chars


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: python wc.py [FILE]", file=sys.stderr)
        return 2
    if args:
        path = args[0]
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            print(f"wc.py: {path}: {e.strerror}", file=sys.stderr)
            return 1
        print(*count(data), path)
    else:
        print(*count(sys.stdin.buffer.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
