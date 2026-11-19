# Style guide

How text reads in this repo: commits, issues, PRs, review comments, code comments and docs. Humans and agents follow the same rules, and reviewers check them during review. The examples follow a hypothetical script, `scripts/install-hooks`, that isn't in this repo.

## Core rules

1. **Lead with the point.** The first sentence says what the reader most needs: the change, the problem, the rule.
2. **Say why; let the artifact show what.** The diff, the code and the error text already show what. Add the reason they can't show.
3. **Link, don't restate.** Point to the issue, doc or line that holds a fact, and keep the fact there.
4. **Concrete over general.** Use names, paths, numbers and exact error text.
5. **Lists for parallel items, prose for reasoning.** Steps, options and criteria go in lists. A chain of because and therefore goes in sentences.
6. **Cut what the reader would skip.** Drop preamble, recaps and filler. Keep every detail the reader needs to act.

## Register

Write plainly and neutrally. Leave out praise, apology, polite hedging and emoji. When something is uncertain, say so once and say exactly what is unknown.

Write one paragraph per line and leave body lines unwrapped.

## Commits

The PR title becomes the subject of the commit on `main`, and the PR description becomes its body. Their format, the 64-character title limit and the `BREAKING CHANGE:` footer live in [`commits.md`](workflow/commits.md).

Commits on an Issue branch have no required format. Write them like this:

- The subject is at most 72 characters.
- The body is optional. Add one only to say why, when the subject and the diff don't make it obvious.
- References go in trailers at the end, such as `Refs #<issue>` or `Co-Authored-By:`.

```text
fix(hooks): replace hook links that already exist

`ln -s` exits 1 when the link already exists, which aborted every re-run of install-hooks.

Refs #<issue>
```

## Issues

Lead with the need in one or two sentences. Then give the evidence: error text, repro steps, links. Keep any proposed solution in its own section, apart from the problem.

````markdown
`install-hooks` aborts when it runs a second time in the same clone.

`ln -s` exits 1 for a hook link that already exists:

```text
ln: failed to create symbolic link '.git/hooks/pre-commit': File exists
```

Repro: run `scripts/install-hooks` twice.

## Proposed fix

Use `ln -sf`, so a re-run replaces the link instead of failing.
````

## PRs

Fill the description template in [`commits.md`](workflow/commits.md#pr-description). Summarize the change as a whole and why it was made, and give the concrete command or check that verified it. Leave out a file-by-file changelog; the diff is that list.

```markdown
Closes #<issue>

## What and why

`install-hooks` now replaces hook links that already exist instead of failing, so it can run again after a hook is added.

## How verified

Ran `scripts/install-hooks` twice in a fresh clone. The second run exited 0, and `.git/hooks/pre-commit` still pointed at `scripts/pre-commit`.
```

## Review comments

One issue per comment. State the problem, why it matters and a suggested fix. Prefix the comment `blocking:` if it must be fixed before merge, or `nit:` if it's optional. An unmarked comment counts as `blocking:`, and so does a question that must be answered before merge.

```markdown
blocking: `prune` removes the worktree before checking for uncommitted changes, so a dirty worktree loses its work. Run `git -C <worktree> status --porcelain` first and skip the worktree if it prints anything.
```

Reply in one line, with one of the [final replies](workflow/review.md#final-replies).

## Code comments

Say why: the intent, a constraint, a gotcha. One line is the default, not a cap. History belongs in commits, and removed code is deleted, not commented out.

```sh
ln -sf ../../scripts/pre-commit .git/hooks/pre-commit # relative, so the link still resolves after the clone moves
```

## Docs

Docs follow the core rules. Docs that agents read, such as `AGENTS.md` and `docs/workflow/`, also follow these:

- **Context pointers.** Each `AGENTS.md` entry names one doc and when to read it, so an agent loads only what its task needs.
- **Positive phrasing.** State what to do. Name a thing to avoid only alongside what to do instead.
- **Single source of truth.** Each rule lives in one doc. Other docs link to it.

```markdown
Run `scripts/install-hooks` once after cloning: `.git/hooks/` isn't tracked, so a fresh clone has no hooks and its commits skip the checks.
```

## Accelerators (optional)

Delete this section if the repo uses no Accelerators.

- mattpocock-skills `writing-for-agents` helps write docs for agents. The rules above still apply.
