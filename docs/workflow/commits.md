# Commits and PRs

What lands on `main` is one squash commit per PR. Its subject is the PR title and its body is the PR description, so write both as the commit message.

## Merging

- PRs merge by squash only. Merge commits and rebase merges are off.
- The squash message is the PR title plus the PR description. GitHub appends a space and `(#<PR>)` to the subject.
- Commits on an Issue branch are free-form. Only the PR title has to follow the format below.

## PR title

The title is a [Conventional Commit](https://www.conventionalcommits.org/) header of at most 64 characters, so the squash subject stays within 72 once GitHub appends a space and `(#<PR>)` (for PR numbers up to 9999):

```text
<type>[(<scope>)][!]: <subject>
```

- `type` is one of `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- `scope` is optional, with no fixed list.
- `!` marks a breaking change (see below).

The `pr-title` job in `ci.yml` checks the type and the length, and re-runs whenever the title is edited. `feat: add x` and `feat!: drop y` pass; `update stuff` fails. Dependabot PRs skip the length check, because Dependabot writes its own titles.

GitHub's **Revert** button titles its PR `Revert "<original title>"`, which fails `pr-title`. Retitle it `revert: <original subject>`, shortened to fit 64 characters if needed.

## PR description

New PRs open with this template:

```markdown
Closes #

## What and why

## How verified
```

- `Closes #<issue>` names the one issue this PR closes. The `issue-link` check enforces it; see [`issues.md`](issues.md#one-issue-per-pr).
- **What and why** says what changed and why, for someone reading `main`'s history later.
- **How verified** says what you ran or checked, and what you saw.

End the description with any footers, as its last paragraph, one per line. Write each footer in git's `Token: value` trailer form, such as `Refs: #<issue>`. That paragraph becomes the squash commit's trailers, and one line outside the form, such as `Refs #<issue>`, can stop git parsing any of them.

## Acceptance criteria

Before a PR is ready for review, the author updates the acceptance criteria in its issue's body, so that once the PR closes the issue it still shows which criteria were met and which were deferred. GitHub leaves an issue's task list as it is when a PR closes it.

- Tick each criterion the PR meets. **How verified** says how each was checked.
- Leave a criterion the PR defers unticked, and append the [Follow-up](issues.md#follow-ups) that carries it, such as `→ #61`.

Every criterion ends ticked or pointing at its Follow-up. Edit the body with `gh issue edit <n> --body-file <file>`, starting from `gh issue view <n> --json body --jq .body`.

## Breaking changes

Mark a breaking change in both places:

1. `!` before the colon in the title, such as `feat!: drop the v1 config format`.
2. A `BREAKING-CHANGE: <what breaks and what to do instead>` footer at the end of the description.

Spell the footer with a hyphen, not as `BREAKING CHANGE:`. Git doesn't accept a space in a trailer token, so with the space git parses none of the footer paragraph as trailers, and the squash commit loses its `Co-Authored-By:`. Conventional Commits and release-please treat the two spellings the same.

Write either spelling only as a footer. Anywhere else in the description it still counts and still bumps the version.

## Agent attribution

An agent-assisted PR ends its description with the provider's `Co-Authored-By:` trailer, so the attribution survives the squash:

```text
Co-Authored-By: <agent name> <provider's no-reply address>
```

Use the exact line the provider gives. Put it in the footer paragraph, with any `BREAKING-CHANGE:` footer.

## Accelerators (optional)

Delete this section if the repo uses no Accelerators.

- mattpocock-skills `pr` writes the PR description. It fills this template; the rules above still apply.
- Nothing maps onto the PR title or the commit format.
