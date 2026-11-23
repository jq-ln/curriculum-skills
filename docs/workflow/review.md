# Review

How a PR is reviewed, answered and merged. The protocol is bounded so that reviews converge: at most two agent [Review rounds](#review-rounds), every thread ends with a [final reply](#final-replies), and disputes go to the maintainer instead of looping between agents.

It names three roles, not accounts; one account may act in all three:

- **Author**: the session that works the issue and opens its PR.
- **Reviewer**: an agent session the maintainer starts to review the PR.
- **Maintainer**: the final reviewer, and the only one who merges.

Use [`threads`](../../.github/scripts/threads) for every thread operation: listing, replying, editing a reply, resolving and the end-state check. `gh` has no command to resolve a thread, and hand-written GraphQL loops have failed silently.

```sh
.github/scripts/threads list <pr>                            # every thread, resolved ones included, in full
.github/scripts/threads reply <thread> "Fixed in <sha>"      # <thread> is the PRRT_... id list prints
.github/scripts/threads edit <comment> "Declined: ..."       # <comment> is a comment URL list prints
.github/scripts/threads resolve <thread>                     # one thread per call
.github/scripts/threads resolve --accept-decline <thread>    # a declined blocker; see Who resolves
.github/scripts/threads check <pr>                           # prints counts; exits 1 while a thread lacks a final reply
```

## Review rounds

A Review round is one agent review of the PR plus the author's response pass that answers it.

- **Round 1** may raise anything.
- **Round 2** may raise only blockers introduced by round 1's fix commits, or a blocker round 1 missed, stating why it was missed. It raises no nits.
- **After round 2** the loop stops and the PR goes to the maintainer, whatever is still open.

Round 2 starts only when `threads check <pr>` passes, so every round-1 thread has a final reply. The Release PR has no Review rounds; agents never review or merge it.

## Markers

Every review comment is marked `blocking:` or `nit:`, as [`style.md`](../style.md#review-comments) defines them; there are no other markers. A blocker must be fixed, moved or settled before merge. A nit is the author's call.

## Final replies

Every thread ends with one of these, as the first line of its latest comment:

- `Fixed in <sha>`: the commit that fixes it, as at least 7 lowercase hex characters like `git log --oneline` prints, optionally followed by `: <what changed>`.
- `Moved to #<n>`: a [Follow-up](issues.md#follow-ups) now holds the work.
- `Declined: <reason>`: one reason, in the same line.

A later comment in the thread, such as a maintainer's question, reopens it until the author answers with a final reply again, even if the thread is resolved. So accept a reply by resolving the thread, without replying to it. If a later change contradicts an earlier reply, edit that reply with `threads edit` rather than adding a second one, so the thread still states the outcome.

`threads check` sees threads only. Findings in a review's body are answered in a PR comment (see [Author](#author)), and the author confirms each has a final reply.

## Who resolves

- The author resolves `Fixed` and `Moved` threads, and declined `nit:` threads, once it has replied.
- A declined `blocking:` thread stays open until its opener or the maintainer resolves it, with `threads resolve --accept-decline`. The reviewer session that opened it has ended by then, so the next round's reviewer acts as its opener. The author never passes `--accept-decline`. The ruleset requires every conversation to be resolved, so an open declined blocker holds the merge until someone rules on it.
- Nothing is resolved without a final reply; `threads resolve` refuses.
- Resolve one thread at a time, each after reading it. Never resolve threads in a loop or in bulk to unblock the merge: resolving means the thread is settled.

## Reviewer

The maintainer starts each reviewer in a fresh session. It is never the author's session or a subagent the author spawned, so no one reviews their own work.

1. **Read everything first.** Read the linked issue (`gh issue view <n> --comments`), every thread with `threads list <pr>`, resolved ones included, and the PR's earlier reviews and comments (`gh pr view <pr> --comments`). Raise a settled point again only by citing what is new.
2. **Check the acceptance criteria.** Confirm that each ticked criterion in the issue is met by the diff, and that each unticked one names its Follow-up, as [`commits.md`](commits.md#acceptance-criteria) describes. Raise a mismatch as a `blocking:` finding in the review body.
3. **Rule on declined blockers** (round 2). For each open declined `blocking:` thread, either accept it with `threads resolve --accept-decline <thread>`, or [escalate](#escalation) at once. Don't argue it again in the thread.
4. **Post the round as one review.** Each round is exactly one GitHub review of type `COMMENT`, whose body starts `Round <n>`. Findings on a diff line are its comments. Findings with no diff line go in its body as a list, each with its marker, never only in chat:

   ```sh
   gh api --method POST repos/{owner}/{repo}/pulls/<pr>/reviews --input - <<'EOF'
   {
     "event": "COMMENT",
     "body": "Round 1\n\n- blocking: <finding with no diff line>",
     "comments": [
       { "path": "docs/workflow/issues.md", "line": 42, "side": "RIGHT", "body": "nit: <finding>" }
     ]
   }
   EOF
   ```

5. **Stop.** The reviewer never pushes, approves or merges, and checks code out only as in [Reviewer worktrees](branches.md#reviewer-worktrees).

## Author

The author answers each round with one response pass and one push:

1. **Read everything.** Read the linked issue, every thread with `threads list <pr>`, resolved ones included, and the round's review body. Raise a settled point again only by citing what is new.
2. **Fix within scope.** Fix what [the PR may touch](issues.md#what-a-pr-may-touch). Out-of-scope work becomes a [Follow-up](issues.md#follow-ups). If a fix changes which criteria the PR meets, update the issue's ticks as [`commits.md`](commits.md#acceptance-criteria) describes. Push once, after all the fixes.
3. **Reply to every thread** with a [final reply](#final-replies), using `threads reply`. Answer the findings in the review body in one PR comment, quoting each finding with its final reply.
4. **Resolve** what the author may, as in [Who resolves](#who-resolves).
5. **Check.** Run `threads check <pr>` and report the counts it prints, as printed. The pass isn't done until it passes.

When the reviewer escalates, or a round-2 blocker can't be settled in the PR, the author [escalates](#escalation) too.

## Escalation

An agent escalates by handing the open threads to the maintainer and stopping:

1. Post one PR comment that lists each open thread: its link, its point in one line, and the author's and the reviewer's positions.
2. Request the maintainer's review with `gh pr edit <pr> --add-reviewer <login>`. GitHub can't request a review from the PR's own author, so if the PR was opened from the maintainer's account, the comment is the request.
3. Stop. Don't reply in the threads again or start another round.

## Maintainer

- Starts each reviewer session, fresh, and decides whether to start round 2.
- Comments with the same markers. The round cap doesn't apply to the maintainer's comments, and the author answers them like any other thread.
- Rules on escalations, resolving each thread or answering in it.
- Merges, as its own step after review. Agents never merge, and the issue closes through `Closes #<n>` on merge, never by hand before it (see [`issues.md`](issues.md#closing)).

## Accelerators (optional)

Delete this section if the repo uses no Accelerators.

- mattpocock-skills `code-review` can do the reviewer's reading and finding. The reviewer still posts its findings as one `Round <n>` review, with the markers above.
- Nothing maps onto the author's response pass.
