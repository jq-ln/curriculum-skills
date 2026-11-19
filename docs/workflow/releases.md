# Releases

[release-please](https://github.com/googleapis/release-please) cuts this repo's releases from the squash commits on `main`. [`release.yml`](../../.github/workflows/release.yml) runs it on every push to `main`, configured by [`release-please-config.json`](../../release-please-config.json), with the last released version in [`.release-please-manifest.json`](../../.release-please-manifest.json).

## Versions

Versions are `0.n.m` until 1.0:

- A breaking change bumps `n` and resets `m`: `0.3.2` becomes `0.4.0`. A PR marks one as [`commits.md`](commits.md#breaking-changes) says.
- Every other release bumps `m`: `0.3.2` becomes `0.3.3`, however many `feat` and `fix` commits it holds.

The first release is `0.0.1`, even when a breaking change lands before it: a manifest at `0.0.0` means nothing has been released, and release-please starts at `initial-version` in the config.

From 1.0 on, the same config follows plain semver: breaking bumps the major, `feat` the minor, `fix` the patch. Nothing in the config changes at 1.0.

The release type is `simple`: the version lives in `version.txt`. A repo that ships a package can switch `release-type` in the config, such as to `node` to version `package.json`.

## Changelog

release-please writes `CHANGELOG.md` from the squash subjects, which are the PR titles. Only these types show, each under its own heading:

| Type | Heading |
| --- | --- |
| `feat` | Features |
| `fix` | Bug Fixes |
| `perf` | Performance Improvements |
| `revert` | Reverts |

A breaking change of any type is also listed under a breaking-changes heading. The other types are left out, and a Release PR opens only once `main` has a commit that shows in the changelog.

## The Release PR

release-please keeps one Release PR open on the `release-please--branches--main` branch and rewrites it on every push to `main`. It bumps `version.txt` and the manifest and adds the next version's section to `CHANGELOG.md`.

- Only the maintainer merges the Release PR, whenever they choose. There are no release or hotfix branches: a hotfix is a `fix:` PR, then a merge of the Release PR.
- To correct the release notes, the maintainer edits the Release PR's `CHANGELOG.md` and description just before merging it. The next push to `main` rewrites the Release PR and drops earlier edits.
- release-please labels the Release PR `autorelease: pending`, then `autorelease: tagged` once released, and finds the merged Release PR by those labels. They aren't triage labels; leave them on it.

Merging the Release PR runs `release.yml` again, which tags the merge commit `v0.n.m`, with no component name, and publishes a GitHub Release holding that version's notes.

By default, the workflow's `GITHUB_TOKEN` opens the Release PR, and GitHub starts no workflows for events made with that token. So `ci` never runs on the Release PR, and the maintainer merges it through the Repository admin bypass. [`RELEASE_PLEASE_TOKEN`](#optional-release_please_token) makes the checks run.

## Agents and releases

release-please owns the release files and the Release PR. Agents:

- leave `CHANGELOG.md`, `version.txt` and `.release-please-manifest.json` to release-please, and change what a release says through the PR titles of the work that goes into it
- leave the Release PR to the maintainer: agents never review it, merge it or push to its branch

## 1.0

The maintainer cuts 1.0 with a PR they author themselves, never an agent. Its description ends with this footer, which survives the squash:

```text
Release-As: 1.0.0
```

The next Release PR then proposes `1.0.0`.

## Optional: `RELEASE_PLEASE_TOKEN`

Set a `RELEASE_PLEASE_TOKEN` repository secret to have the Release PR opened by an account whose events start workflows, so `ci` runs on it. Set the `RELEASE_PLEASE_AUTHOR` repository variable to that account's login with it, so the Release PR passes `issue-link` instead of failing with "The PR closes no issue." (see [`issues.md`](issues.md#one-issue-per-pr)).

Create the token on a dedicated release account with Write access to the repo, never on the shared machine account or another account an agent holds a token for. `issue-link` skips every `release-please--*` PR that the `RELEASE_PLEASE_AUTHOR` account opens, and the ruleset protects only `main`, so an agent acting as that account could push such a branch and open a PR that closes no issue. Give agents' tokens no Workflows permission too: a workflow on any branch pushed to the repo can read the secret, so an agent that can push workflow files could take the token through one. Which kind of token depends on who owns the repo, because a fine-grained token reaches only repos owned by its own account or by an organization the account belongs to:

- **Organization-owned repo:** a fine-grained personal access token with the organization as resource owner, limited to this repo, with read and write access to Contents, Issues and Pull requests.
- **Repo owned by a personal account:** a classic personal access token with the `repo` scope. A collaborator's fine-grained token can't select the repo.

Set the variable before the secret, then close the open Release PR, if there is one. Once the secret exists, the next push to `main` rewrites the Release PR with the token, so the variable must already hold the token's login. A PR keeps the author that opened it, though, so the open Release PR stays `github-actions[bot]`'s and fails `issue-link` whatever the variable says; the next run of `release.yml` opens a new one as the token's account. Reading the login from the token rules out a mistyped login, and the chain stops before the secret if the login comes back empty:

```sh
read -rs token # paste the token, then press Enter
login=$(GH_TOKEN=$token gh api user --jq .login) &&
  [ -n "$login" ] &&
  gh variable set RELEASE_PLEASE_AUTHOR --body "$login" &&
  printf %s "$token" | gh secret set RELEASE_PLEASE_TOKEN &&
  gh pr close release-please--branches--main # fails harmlessly if no Release PR is open
unset token login
```

Only the maintainer creates the token. Without the secret, `release.yml` falls back to `GITHUB_TOKEN`. An expired or revoked token doesn't fall back: every run fails with 401, the Release PR stops updating and a merged one is never tagged. Rotate the token before it expires, and when it moves to another account, run the commands above again with the new token, which also closes the old account's Release PR. To return to `GITHUB_TOKEN`, delete both, so the old account loses its `issue-link` skip:

```sh
gh secret delete RELEASE_PLEASE_TOKEN
gh variable delete RELEASE_PLEASE_AUTHOR
```
