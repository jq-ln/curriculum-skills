# CI

Every PR runs [`ci.yml`](../../.github/workflows/ci.yml) when it's opened, reopened, pushed to or edited. Its final job, `ci`, is the only check the ruleset requires. It `needs:` every other job and fails unless all of them succeeded: a failed, cancelled or skipped job fails it. A newer run cancels the PR's older one, so a cancelled run's `ci` fails and the newer run's `ci` is the one that counts.

## Checks

Each check except `pr-title` and `issue-link` runs over the whole repo, not just the changed files.

| Job | What it enforces |
| --- | --- |
| `pr-title` | The PR title is a Conventional Commit with one of the allowed types, using [`action-semantic-pull-request`](https://github.com/amannn/action-semantic-pull-request), and a shell step checks it's at most 64 characters (Dependabot PRs skip this step). See [`commits.md`](commits.md). |
| `issue-link` | The PR closes exactly one open issue of this repo, using [`check-pr-issue`](../../.github/scripts/check-pr-issue). See [`issues.md`](issues.md#one-issue-per-pr). |
| `markdownlint` | Markdown style, using [`markdownlint-cli2`](https://github.com/DavidAnson/markdownlint-cli2) and [`.markdownlint-cli2.jsonc`](../../.markdownlint-cli2.jsonc). MD013 (line length) is off, and `CHANGELOG.md` is skipped because release-please writes it. |
| `lychee` | Relative links in Markdown files resolve to existing files. It runs offline, so remote URLs aren't checked. |
| `actionlint` | Workflow syntax, expressions and `run:` scripts (through shellcheck). |
| `shellcheck` | Every tracked `.sh` or `.bash` file, and every file with an `sh`, `bash`, `dash` or `ksh` shebang. |
| `init-test` | That `.github/scripts/init` still removes the content this repo was created without, using `.template/test-init`. Init deletes both when it runs, so from then on the job passes without checking anything. |

To reproduce a check locally, run its command from the repo root with the version CI uses:

| Tool | Version CI uses |
| --- | --- |
| lychee | `LYCHEE_VERSION` in `ci.yml` |
| actionlint | `ACTIONLINT_VERSION` in `ci.yml` |
| markdownlint-cli2 | The one bundled with the pinned `markdownlint-cli2-action`. The job log's first line names it. |
| shellcheck | The one on the runner image. The job log prints it. |

```sh
# markdownlint (add --fix to fix what it can)
npx markdownlint-cli2@<version> '**/*.md'

# lychee
lychee --offline --no-progress --hidden --extensions md .

# actionlint
actionlint

# shellcheck (needs GNU xargs; the same pipeline as in ci.yml)
git ls-files -z \
  | xargs -0 -r awk 'FNR == 1 { if (FILENAME ~ /\.(ba)?sh$/ || /^#!.*[\/ ](ba|da|k)?sh( |$)/) print FILENAME; nextfile }' \
  | xargs -r -d '\n' shellcheck
```

## Workflow rules

Every workflow in `.github/workflows/`:

- Declares `permissions: {}` at the top level and grants each job only what it needs.
- Pins each action to a full commit SHA, with the version in a trailing comment (`uses: owner/action@<sha> # v1.2.3`).

[Dependabot](../../.github/dependabot.yml) updates pinned actions monthly. It doesn't track lychee (`LYCHEE_VERSION`), actionlint (`ACTIONLINT_VERSION` and `ACTIONLINT_SHA256`) or shellcheck, which comes preinstalled on the runner.

## Adding a job

1. Add the job to `ci.yml` with its own `permissions:` block and SHA-pinned actions.
2. Add its id to the `ci` job's `needs:` list.
3. Leave the ruleset alone: `ci` stays the only required check.

Keep `ci.yml` running on every PR, with no `paths:` filters: a required check that never runs stays pending and blocks the merge. Don't give a job a job-level `if:` either: a skipped job fails `ci`. A job that applies only to some changes decides inside the job whether to do anything, and passes when it has nothing to do.
