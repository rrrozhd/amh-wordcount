# amh-wordcount
Agent Mission Hub end-to-end test: word-count CLI built by agents

Requires Python 3 and uses only the standard library.

```sh
python wc.py input.txt                 # LINES WORDS CHARS FILE
python wc.py --top 3 input.txt          # one COUNT WORD line per ranked word
python wc.py --json input.txt           # one JSON object with counts and file
python wc.py --json --top 3 input.txt   # also include top: [[word, count], ...]
python -m unittest
```

Omit the file to read standard input; JSON then uses `"file": null`.
`--top N` (or `--top=N`) requires a positive integer. Words are split on ASCII
whitespace, decoded as UTF-8 with replacement for invalid bytes, and lowercased
for ranking. Punctuation stays attached. Ranking is by descending frequency,
then alphabetical order; fewer than N distinct words yields fewer entries.

Lines count newline bytes; characters count decoded UTF-8 characters, preserving
both characters in CRLF. `count()` owns these existing semantics. The option
parser feeds `_main_with_options()`, which reads once and selects plain top output
or JSON; `top_words()` supplies the ranking for either format. Without the new
options, `main()` retains the original argument handling and output.

Argument errors return 2 and file errors return 1, with diagnostics on stderr.
There are no dependencies to install or build steps: run `wc.py` directly.
