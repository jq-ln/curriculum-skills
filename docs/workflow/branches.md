# Branches and worktrees

How Issue branches and worktrees are created, kept current, resumed and removed. `main` is the only long-lived branch: every Issue branch starts from it and reaches it only through its issue's PR, as a squash merge (see [`commits.md`](commits.md)). In the names and commands below, `<n>` is the issue number.

## Pruning

At the start of every agent session, before any other work, run [`prune`](../../.github/scripts/prune) from the main checkout:

```sh
.github/scripts/prune
```

It runs `git fetch --prune`, sets `gh`'s default repo to `origin`'s if none is set and `origin` isn't a fork (see [Tracker operations](issues.md#tracker-operations) for why), then removes the worktree and local branch of every Issue branch whose remote branch is gone. A remote branch goes when its PR merges, because GitHub deletes merged head branches, or when the maintainer deletes it on [closing its issue](issues.md#closing). Branches with a live remote branch, or with none ever pushed, stay. It also removes [reviewer worktrees](#reviewer-worktrees) whose PR is no longer open. If the fetch fails, such as offline, it prints `prune: fetch failed, nothing pruned` and exits 0; carry on and run it again later.

To tell finished work from unpushed work, `prune` compares each branch with where it was last pushed: its remote-tracking branch, or, if something such as `fetch.prune` already deleted that, the head of its PR on GitHub.

`prune` keeps a finished branch, and prints why, when:

- it has commits that were never pushed. Push or discard them.
- it can't find where the branch was last pushed, so it can't tell. Check the branch, then remove it with the commands it prints: `git worktree remove <path>`, then `git branch -D <branch>`, because git won't delete a branch that a worktree has checked out.
- its worktree has uncommitted changes or untracked files. Commit or discard them.
- it's checked out in the main checkout, or `prune` is running in its worktree. Switch the main checkout to `main`, or run `prune` from the main checkout.

It keeps a [reviewer worktree](#reviewer-worktrees) whose PR isn't open, and prints why, when:

- it can't read the PR's state, such as when `gh` isn't logged in or the PR isn't among the 200 most recent. Check the PR, then run `git worktree remove .worktrees/pr-<n>`.
- the worktree has uncommitted changes or untracked files. A reviewer's findings go in its review, so remove it with `git worktree remove --force .worktrees/pr-<n>`.
- `prune` is running in it. Run `prune` from the main checkout.

Then run `prune` again.

## Issue branches

Each issue gets one Issue branch, named `<type>/<n>-<slug>`, such as `feat/42-pr-title-lint`:

- `<type>` is a Conventional Commit type from [`commits.md`](commits.md#pr-title).
- `<slug>` is a few words of kebab-case.

The name is a convention, not a CI check. Bot branches, such as Dependabot's and the Release PR's, keep their own names.

Create the branch right after [claiming the issue](issues.md#claiming-and-abandoning), from the latest `main`, with `gh issue develop`, so it shows in the issue's Development panel:

```sh
gh issue develop <n> --name <type>/<n>-<slug> --base main
```

Push early, and at the latest when the session stops, so the next claimant can resume the work.

## Worktrees

Agents always work in a worktree at `.worktrees/<n>-<slug>/`, one per issue, and leave the main checkout on `main`, so parallel sessions in one clone never share a checkout. Humans may use one too. `.worktrees/` is gitignored.

```sh
git fetch origin
git worktree add .worktrees/<n>-<slug> <type>/<n>-<slug>
```

`git worktree add` creates the local branch tracking `origin/<type>/<n>-<slug>`, so a plain `git push` works from the worktree. Once the branch is finished, `prune` removes the worktree.

## Staying current

Before the PR opens, rebase onto `main` as often as you like:

```sh
git fetch origin
git rebase origin/main
git push --force-with-lease
```

Once the PR is open, merge `main` in instead and push only new commits, because review threads anchor to commits:

```sh
git fetch origin
git merge origin/main
git push
```

The ruleset doesn't require a branch to be up to date before it merges.

## Resuming an abandoned issue

[Abandoning an issue](issues.md#claiming-and-abandoning) leaves its Issue branch and worktree in place. The next claimant resumes on the branch linked to the issue instead of creating a new one. List it, then work in its worktree, adding one as in [Worktrees](#worktrees) if this clone has none:

```sh
gh issue develop --list <n>
```

When an issue is [handed back](issues.md#handing-back-an-issue-thats-too-big) and re-cut, its partial branch is reference only. Each new Ticket gets a fresh Issue branch from `main` and may cherry-pick from the partial branch, which the maintainer deletes when [closing the Spec](issues.md#closing-a-spec). A handed-back standalone issue becomes the Spec, so its partial branch is the Spec's own Issue branch.

## Reviewer worktrees

A reviewer that needs to run a PR's code checks it out, detached, into `.worktrees/pr-<n>/`, where `<n>` is the PR number:

```sh
git fetch origin pull/<n>/head
git worktree add --detach .worktrees/pr-<n> FETCH_HEAD
```

The reviewer's findings go in its review, not in commits to the branch. When its Review round ends, it removes the worktree; if the session ends first, the next `prune` removes it once the PR closes:

```sh
git worktree remove .worktrees/pr-<n>
```
