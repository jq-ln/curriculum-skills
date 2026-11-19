# Issues

How issues are filed, triaged, sized, worked and closed in this repo. Issues live in GitHub Issues; use the `gh` CLI for every tracker operation (see [Tracker operations](#tracker-operations)).

## Types

Every issue has one of GitHub's native issue types, which says what kind of change it is:

- **Bug**: something doesn't work as it should.
- **Feature**: something new the repo should do.
- **Task**: anything else, such as docs, CI or cleanup.

The type is independent of the hierarchy: a Bug can be a Spec, and its Tickets can be Tasks. There are no kind labels such as `bug` or `enhancement`.

Humans file issues through the Bug, Feature and Task forms in [`.github/ISSUE_TEMPLATE/`](../../.github/ISSUE_TEMPLATE/). Each form sets its type and applies `needs-triage`, and blank issues are off. There's no Spec form: a Spec is a parent issue of any type. `gh` skips the forms, so an agent sets the type and the label itself.

The forms and `--type` need the repo owner to have issue types named Bug, Feature and Task. GitHub creates them by default; an organization that renamed or deleted one restores it in its organization settings, because `setup` can't manage issue types.

## Triage labels

There are exactly four triage labels:

| Label | Meaning |
| --- | --- |
| `needs-triage` | The maintainer needs to evaluate this issue. |
| `needs-info` | Waiting on the reporter for more information. |
| `ready-for-agent` | Fully specified, ready for an agent to work on alone. |
| `ready-for-human` | Needs a human to implement it. |

Every open issue carries exactly one of them, except an approved Spec, which carries none. A repo may add area labels, but no other triage states, and no `wontfix` or `duplicate` labels: those are close reasons (see [Closing](#closing)).

New standalone issues and Specs start at `needs-triage`, whoever files them. The maintainer's one queue is `is:open label:needs-triage,needs-info sort:updated-desc`. A `needs-info` issue stays in it, so the reporter's reply brings it back to the top, and the maintainer triages it again.

### Who changes triage labels

Only the maintainer triages: moving an issue from `needs-triage` to `needs-info` or a `ready-*` label, approving a Spec, or closing an issue as not planned or duplicate.

Agents may add `needs-triage`, when filing an issue or a Follow-up, or when handing back an issue, which also removes its `ready-*` label (see [Handing back an issue that's too big](#handing-back-an-issue-thats-too-big)). Agents never remove `needs-triage` and never apply `ready-*`, except to Tickets cut at the maintainer's direction (see [Specs and Tickets](#specs-and-tickets)). To suggest a triage decision, an agent comments on the issue.

## Specs and Tickets

A Spec is a parent issue for a change too big for one PR. Its Tickets are its sub-issues. The hierarchy is two levels deep: a Ticket has no sub-issues of its own. Work that fits one PR is a standalone issue, with no parent.

1. A Spec is filed at `needs-triage`, like any new issue.
2. The maintainer approves it by removing `needs-triage`. From then on the Spec has no triage label and no assignee.
3. Tickets cut from an approved Spec, by the maintainer or at the maintainer's direction, are born `ready-for-agent` or `ready-for-human`: approving the Spec was their triage.
4. A Spec gets no blocking edge to its own Tickets; the sub-issue relation already says it waits for them.

### Closing a Spec

Each time a Ticket closes, by a merged PR or as not planned or duplicate, the maintainer runs the [open-Tickets query](#sub-issues) on its Spec. The check runs after the close, so the last Ticket to close always sees an empty result, even when two Tickets close at the same time. When the query prints nothing, the maintainer checks the Spec against what was built, then either:

- closes the Spec with a comment, and deletes the partial branch of each issue [handed back](#handing-back-an-issue-thats-too-big) under it: the Spec's own Issue branch, if the Spec was a standalone issue that was handed back, and the branch of each Ticket that was replaced by smaller Tickets (see [`branches.md`](branches.md#resuming-an-abandoned-issue)), or
- files the missing Ticket as a sub-issue of the Spec, born `ready-*` like any Ticket the maintainer cuts.

## Scope

Every PR closes exactly one open issue, and every standalone issue or Ticket that's done closes through exactly one PR (see [Closing](#closing)). There's no exemption for small changes; only Dependabot's PRs and the Release PR close no issue.

### One issue per PR

The PR description's `Closes #<issue>` line names the issue (see [`commits.md`](commits.md#pr-description)). The `issue-link` job in [`ci.yml`](../../.github/workflows/ci.yml) runs [`check-pr-issue`](../../.github/scripts/check-pr-issue) on the PR events in its `types:` list, `edited` included, so editing the body re-runs it. Other PR events, such as marking a draft ready for review, don't run it. It reads the issues GitHub will close when the PR merges, and fails `ci` unless there is exactly one, it's an open issue of this repo, and the body names it with a closing keyword:

- GitHub decides which references close an issue; see [Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue). `Closes #5, #6` closes only #5, and references in code don't count.
- Mention other issues without a closing keyword, such as `Refs #6`.
- An issue linked from the PR's sidebar also closes on merge, so it counts toward the one. The body still needs its `Closes` line, because only the body lands in the squash commit.
- The PR must target the default branch, because GitHub ignores closing keywords in PRs into any other branch. A stacked PR fails until its base merges and GitHub retargets it to the default branch, which re-runs the check.
- Closing the issue and changing a sidebar link send no PR event, so neither re-runs the check. If either happens after the check passed, the green `ci` goes stale; re-run the job before merging to catch it.
- Dependabot's PRs skip the check and pass. So does the Release PR, but only when its head branch is `release-please--*` and its author is the account in the `RELEASE_PLEASE_AUTHOR` repository variable; a branch name alone doesn't skip it. Any other PR is checked, including one opened by an agent's machine user or GitHub App.

### Size

An issue is the right size when one agent session can finish it and one reviewer can review it in one sitting. There's no numeric cap. Work that needs more than one PR is a [Spec](#specs-and-tickets).

Each Ticket is a vertical slice: it delivers one thin piece end to end, and merging it leaves `main` releasable.

### What a PR may touch

A PR contains what its issue needs plus the direct consequences: tests, docs and glossary entries for the change. Fixing a typo or comment in a line the PR already touches is fine. Drive-by refactors, unrelated fixes and formatting churn are not; they become Follow-ups.

### Handing back an issue that's too big

When an issue turns out bigger than one session or one review, stop and hand it back for a re-cut instead of growing the PR:

1. Comment on the issue where the work got to, linking the branch that holds any partial work.
2. Remove the `ready-*` label and add `needs-triage`.
3. Unassign yourself.
4. Stop. Don't propose the split; the maintainer re-cuts the issue. A standalone issue becomes a Spec with Tickets, and a Ticket is replaced by smaller Tickets under the same Spec.

A session that only ran out of time abandons the issue instead; see [Claiming and abandoning](#claiming-and-abandoning).

### Follow-ups

Out-of-scope work found while working an issue becomes a Follow-up, not part of the current PR:

1. File it as a new issue with `needs-triage`.
2. Comment on the current issue or PR linking the Follow-up.
3. Join the two with a blocking edge, in the direction below. Never make a Follow-up a sub-issue.

A review comment may point at files outside the PR as evidence. If the change in the PR is wrong, fix it in the PR. If the change is right and another file is now inconsistent with it, file a Follow-up.

### Contradiction blocks, drift follows

The direction of a Follow-up's blocking edge depends on what merging the current PR alone would leave on `main`:

- **Contradiction blocks.** If `main` would be contradictory or broken, the Follow-up blocks the current issue, and lands first.
- **Drift follows.** If the inconsistency is cosmetic, such as format drift, the current issue blocks the Follow-up, which lands after.

If a blocking Follow-up can only land after the current PR's content, the two can't be ordered: hand the current issue back for a re-cut instead.

## Claiming and abandoning

Claiming an issue means assigning yourself; the assignee is the claim. Then create its Issue branch and worktree, as [`branches.md`](branches.md#issue-branches) describes.

Abandoning an issue means unassigning yourself, with a comment saying where the work got to. The labels stay as they are; for the Issue branch, see [`branches.md`](branches.md#resuming-an-abandoned-issue). The maintainer may unassign a stale claim the same way.

## Closing

A standalone issue or Ticket is done when a merged PR closes it through `Closes #<issue>` in its description (see [`commits.md`](commits.md#pr-description)).

An issue that won't be done is closed with a reason instead of a label:

- **Not planned**: the maintainer decided against it.
- **Duplicate**: another issue already covers it. Link the other issue.

When closing an issue as not planned or duplicate, the maintainer also deletes its Issue branch, if it has one, so [`prune`](branches.md#pruning) can remove its worktree. The exception is a Ticket [handed back](#handing-back-an-issue-thats-too-big) and replaced by smaller Tickets: its partial branch stays until [its Spec closes](#closing-a-spec), because the new Tickets may cherry-pick from it. The commands are in [Claiming, commenting and closing](#claiming-commenting-and-closing).

## Tracker operations

These commands were checked with `gh` 2.104. On an older `gh` without a `gh issue edit` flag, use the REST call shown. `gh issue create` flags have no REST fallback here: create the issue without the flag, then use the `edit` fallback. `gh` targets the clone's default repo, and fills in `{owner}` and `{repo}` in `gh api` paths. [`prune`](branches.md#pruning) sets it to `origin`'s repo when none is set, and `setup` always does. Without a default, `gh` prefers an `upstream` remote, so in a Derived repo whose `upstream` is the Template, `gh issue edit <n>` would edit the Template's issue. In a fork's clone that preference is right, because `upstream` is the repo the fork's PRs target, so `prune` leaves it without a default.

REST calls that take another issue (`sub_issue_id`, `issue_id`) need its database id, not its `#number` or `node_id`: `gh api repos/{owner}/{repo}/issues/<n> --jq .id`.

### Filing and reading

```sh
# File an issue (heredoc for multi-line bodies)
gh issue create --type Task --label needs-triage --title "..." --body-file - <<'EOF'
...
EOF

# Read an issue, with its comments
gh issue view <n> --comments

# The maintainer's queue
gh issue list --search "label:needs-triage,needs-info sort:updated-desc"

# Unassigned issues ready for an agent
gh issue list --label ready-for-agent --search "no:assignee"
```

GitHub shares one number space across issues and PRs, so a bare `#42` may be either. Try `gh issue view 42`, and fall back to `gh pr view 42`.

### Setting the type

```sh
gh issue edit <n> --type Bug
# older gh:
gh api --method PATCH repos/{owner}/{repo}/issues/<n> -f type=Bug
```

### Labels

```sh
# Maintainer only: triage an issue
gh issue edit <n> --remove-label needs-triage --add-label ready-for-agent
```

### Sub-issues

```sh
# File a Ticket under a Spec, or attach an existing issue to it
gh issue create --parent <spec> ...
gh issue edit <spec> --add-sub-issue <ticket>
# older gh:
gh api --method POST repos/{owner}/{repo}/issues/<spec>/sub_issues -F sub_issue_id=<ticket-db-id>

# A Spec's open Tickets
gh api --paginate repos/{owner}/{repo}/issues/<spec>/sub_issues --jq '.[] | select(.state == "open") | .number'
```

### Blocking

Blocking edges are GitHub's native issue dependencies.

```sh
# <n> is blocked by <blocker>
gh issue edit <n> --add-blocked-by <blocker>
gh issue create --blocked-by <blocker> ...
# older gh:
gh api --method POST repos/{owner}/{repo}/issues/<n>/dependencies/blocked_by -F issue_id=<blocker-db-id>

# Number of open blockers: 0 means unblocked
gh api repos/{owner}/{repo}/issues/<n> --jq .issue_dependencies_summary.blocked_by
```

### Claiming, commenting and closing

```sh
gh issue edit <n> --add-assignee @me        # claim
gh issue comment <n> --body "..."
gh issue edit <n> --remove-assignee @me     # abandon, after the comment

gh issue close <n> --comment "..."                      # a Spec whose Tickets are done
gh issue close <n> --reason "not planned" --comment "..."
gh issue close <n> --duplicate-of <other>
gh issue develop --list <n>                             # its branch, to delete when closing as not planned or duplicate
gh issue develop --list <handed-back n>                 # at a Spec close: the partial branch of the Spec itself or of a handed-back Ticket
git push origin --delete <branch>
```

## Accelerators (optional)

Delete this section if the repo uses no Accelerators. The conventions above win any conflict with a skill.

mattpocock-skills:

- **Triage roles** map 1:1 onto the [triage labels](#triage-labels). The `wontfix` role is closing as not planned.
- **"Publish to the issue tracker"** means filing an issue as in [Filing and reading](#filing-and-reading). **"Fetch the relevant ticket"** means `gh issue view <n> --comments`.
- **PRs as a request surface: no.** `triage` reads this flag. External PRs aren't triaged as feature requests.
- **`to-spec`** files a Spec. **`to-issues`** cuts its Tickets; its tracer-bullet slicing matches the vertical-slice rule.
- **`wayfinder`** isn't a convention of this repo. Its map and child issues aren't Specs and Tickets, even though they're joined as sub-issues.
