"""Count lines, words and characters, like the Unix wc command.

Usage:
    python wc.py FILE   prints "LINES WORDS CHARS FILE"
    python wc.py        reads standard input and prints "LINES WORDS CHARS"
    python wc.py --top N [FILE]
                        prints the N most frequent words as "COUNT WORD" lines
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


def top_words(data, n):
    """Return the n most frequent words of raw bytes as (word, count) pairs.

    Words are the same whitespace-separated tokens count() uses, decoded as
    UTF-8 and compared case-insensitively (lowercased). Pairs are ordered by
    count, highest first, with ties in alphabetical order.
    """
    counts = {}
    for token in data.split():
        word = token.decode("utf-8", errors="replace").lower()
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]


OPTIONS_USAGE = "usage: python wc.py [--top N] [FILE]"


def _uses_options(args):
    return any(a == "--top" or a.startswith("--top=") for a in args)


def _parse_options(args):
    """Parse [--top N | --top=N] [FILE]; return (top, path) or None if invalid."""
    top = None
    path = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--top" or arg.startswith("--top="):
            if top is not None:
                return None
            if arg == "--top":
                if i + 1 >= len(args):
                    return None
                value = args[i + 1]
                i += 1
            else:
                value = arg[len("--top="):]
            try:
                top = int(value)
            except ValueError:
                return None
            if top < 1:
                return None
        elif path is None:
            path = arg
        else:
            return None
        i += 1
    return top, path


def _read(path):
    """Return (data, error_status): bytes from path or stdin."""
    if path is None:
        return sys.stdin.buffer.read(), None
    try:
        with open(path, "rb") as f:
            return f.read(), None
    except OSError as e:
        print(f"wc.py: {path}: {e.strerror}", file=sys.stderr)
        return None, 1


def _main_with_options(args):
    parsed = _parse_options(args)
    if parsed is None:
        print(OPTIONS_USAGE, file=sys.stderr)
        return 2
    top, path = parsed
    data, status = _read(path)
    if status is not None:
        return status
    for word, n in top_words(data, top):
        print(n, word)
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if _uses_options(args):
        return _main_with_options(args)
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
