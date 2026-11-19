# repo-template

A GitHub template repository that gives a new project its git and GitHub workflow, agent instructions and docs from the first commit. A cold agent of any provider can follow the workflow from [`AGENTS.md`](../AGENTS.md) alone, and humans read the same docs, starting from the [root README](../README.md).

It carries:

- issue types, triage labels, and Specs with Tickets as sub-issues
- one issue per PR, enforced in CI
- an Issue branch per issue, worked in a worktree
- squash merges with Conventional Commit PR titles
- a bounded agent review protocol and a thread-ops script
- release-please Release PRs
- one required `ci` check
- the ruleset, repo settings and labels as code, applied by one `setup` script

Agent skills, such as mattpocock-skills, are optional Accelerators: each workflow doc states its convention first and maps skills onto it in a deletable section.

## Terms

**Template**:
This repository. Its content is either inherited, which every Derived repo keeps, or Template-own, such as this page and [`.template/`](../.template/), which only the Template needs. Inherited docs say "this repo".

**Derived repo**:
A repository created from the Template with GitHub's **Use this template** button. It starts with a copy of the Template's default branch.

## Using the Template

1. Click **Use this template** to create a Derived repo.
2. Wait for the `init` workflow, which runs on that first push. It opens a "Set up this repo" issue, then removes the Template-own content and resets the version to `0.0.0` in one commit.
3. Work through that issue's checklist, the same as the [setup checklist](../.template/setup.md) here.

## Acknowledgements

The Template's workflow conventions and its optional Accelerator mappings build on [mattpocock-skills](https://github.com/mattpocock/skills) by Matt Pocock.
