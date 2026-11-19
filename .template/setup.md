# Set up this repo

Do these steps once, in order. The maintainer closes this issue by hand when the required steps are done. Agents may run `setup` in the maintainer's session, but only the maintainer creates accounts and tokens.

## Required

- [ ] Wait for init to finish: the `init` run in the Actions tab is green. Init opened this issue, then pushes one commit that removes the Template-own content. If the run failed, re-run it from the Actions tab; it doesn't open this issue again. Run `setup` only after the run is green, because its ruleset blocks init's direct push to `main`.
- [ ] Run `setup`. From a clone of the repo, with `gh` signed in as a repo admin and `jq` installed, run `.github/scripts/setup`. It applies to the repo behind `origin` (set `GH_REPO=owner/name` to override) and prints that repo first. It pins `gh`'s default repo in your clone to `origin`'s, so plain `gh` calls don't act on an `upstream` remote. It applies the repo settings, the triage labels and the ruleset in `.github/rulesets/main.json`, and reports each item as changed or already in place. It deletes GitHub's default labels, but keeps any that an issue or PR already uses. Re-running it is safe. A private repo needs a paid plan for the ruleset: on GitHub Free, `setup` applies everything else and then stops with GitHub's error.
- [ ] Replace the placeholder title and description at the top of `README.md` through a normal issue and PR, as `docs/workflow/issues.md` and `docs/workflow/commits.md` describe. It's the repo's first full cycle: the PR passes `ci`, squash-merges and closes its issue.

## Optional

- [ ] A shared machine account for agents, so their work is attributed to it and a human approval can be required:
  1. Create a GitHub account for agents and give it Write access to this repo.
  2. Give each developer's agent a fine-grained token for it as `GH_TOKEN`, as "Agents on a machine account" in `README.md` describes.
  3. Raise `required_approving_review_count` in `.github/rulesets/main.json` to `1` through an issue and PR.
  4. Once that PR merges, run `setup` again to apply the ruleset.
- [ ] `RELEASE_PLEASE_TOKEN` and the `RELEASE_PLEASE_AUTHOR` variable, so `ci` runs on the Release PR and it passes `issue-link`. Create the token on a dedicated release account, not the machine account, as `docs/workflow/releases.md` describes in "Optional: `RELEASE_PLEASE_TOKEN`".
