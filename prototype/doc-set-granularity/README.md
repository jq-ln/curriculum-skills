# Doc set and file granularity: prototype

Throwaway prototype for [Doc set and file granularity](https://github.com/jq-ln/curriculum-skills/issues/5). This branch is never merged.

`split.py` splits `~/Documents/curriculum/git.md` into three flat layouts: one file per Subsection (A), per Section (B) and per Part (C). The generated Curricula are not committed, because this repo never stores Curricula. Regenerate them with:

```sh
python3 -I split.py ~/Documents/curriculum/git.md <out-dir>
```

`COMPARE.md` and `LOADING-{A,B,C}.md` are the outputs the decision was made from: file counts, and the tokens an agent reads to load one Subsection plus its prereqs.

Verdict: layout A. See the resolution comment on the issue.
