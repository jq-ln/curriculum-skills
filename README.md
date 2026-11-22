# curriculum-skills

A Claude Code plugin of skills for building curriculums. Its first skill, [`build-curriculum`](skills/build-curriculum/), researches a subject and writes it as a [Curriculum](GLOSSARY.md#curriculums) in the format of [`docs/curriculum-format.md`](docs/curriculum-format.md).

## Install

The repo is one plugin, `curriculum-skills`, whose skills live in [`skills/`](skills/). Each skill holds a copy of [`docs/curriculum-format.md`](docs/curriculum-format.md) in its `references/`, so a skill directory works on its own wherever it's installed.

Both local routes load the working tree in place, so an edit shows up without a release.

- **Claude Code, one session:** run `claude --plugin-dir /path/to/curriculum-skills`. After an edit, run `/reload-plugins`.
- **Any agent:** symlink each skill into `~/.agents/skills`, which Codex, Cursor, Gemini CLI and Copilot read, and into `~/.claude/skills`, which Claude Code reads. From the repo root:

  ```sh
  mkdir -p ~/.agents/skills ~/.claude/skills
  ln -s "$PWD/skills/build-curriculum" ~/.agents/skills/build-curriculum
  ln -s "$PWD/skills/build-curriculum" ~/.claude/skills/build-curriculum
  ```

  In Claude Code, use one route at a time, so the skill loads once.

## Working in this repo

Humans and agents follow the same docs. Agents start from [`AGENTS.md`](AGENTS.md), which says when to read each of these:

- [`docs/style.md`](docs/style.md): how commits, issues, PRs, review comments, code comments and docs read
- [`docs/workflow/issues.md`](docs/workflow/issues.md): issue types, triage labels, Specs and Tickets, scope and claiming
- [`docs/workflow/branches.md`](docs/workflow/branches.md): Issue branches, worktrees and the `prune` script
- [`docs/workflow/commits.md`](docs/workflow/commits.md): PR titles, PR descriptions and squash merges
- [`docs/workflow/review.md`](docs/workflow/review.md): the review protocol and the thread-ops script
- [`docs/workflow/releases.md`](docs/workflow/releases.md): Release PRs and versioning
- [`docs/workflow/ci.md`](docs/workflow/ci.md): the `ci` check, what each job enforces and how to run it locally
- [`docs/workflow/domain.md`](docs/workflow/domain.md): the glossary and Architecture Decision Records
- [`GLOSSARY.md`](GLOSSARY.md): the project's terms and the workflow's terms

## Agent setup

The repo commits one instruction file, [`AGENTS.md`](AGENTS.md), and no provider config. Each developer wires their agent per clone, using the row for their provider below:

- Shared skills for working on this repo go in `.agents/skills/<name>/SKILL.md`, created when the repo needs its first one. Skills the plugin ships go in `skills/<name>/` instead; see [Install](#install).
- Agents in every provider create worktrees with the commands in [`branches.md`](docs/workflow/branches.md#worktrees), so `prune` can remove them. A provider's own worktree command, such as Claude Code's `--worktree`, makes a branch that isn't an Issue branch, so `prune` never removes it.
- Create the table's per-clone files again in each worktree an agent runs in: `git worktree add` checks out tracked files only. `.git/info/exclude` is shared by every worktree, so its entries go in once.
- Provider-local state goes in `.git/info/exclude`, never in `.gitignore`, so the committed `.gitignore` stays provider-neutral.
- The session hook is optional: it runs [`prune`](.github/scripts/prune), which `AGENTS.md` otherwise asks the agent to run first.

| Provider | Instructions | Skills | `.git/info/exclude` | Optional `prune` hook |
| --- | --- | --- | --- | --- |
| [Claude Code](https://code.claude.com/docs/en/memory#agents-md) ≥ 2.1.277 | Reads `AGENTS.md` natively. Start any `CLAUDE.md` or `CLAUDE.local.md` with `@AGENTS.md`: without that line, either file stops Claude Code reading `AGENTS.md`. | Reads only `.claude/skills/`. Symlink it: `mkdir -p .claude && ln -s ../.agents/skills .claude/skills`. | `.claude/settings.local.json`, `.claude/skills`, `CLAUDE.md`, `CLAUDE.local.md` | [`SessionStart`](https://code.claude.com/docs/en/hooks#sessionstart) in `.claude/settings.local.json` |
| [Codex](https://developers.openai.com/codex/guides/agents-md) | Reads `AGENTS.md` natively. | Reads `.agents/skills/` natively. | `.codex/hooks.json`, `.codex/config.toml`, if you add them | [`SessionStart`](https://developers.openai.com/codex/hooks) in `.codex/hooks.json` (≥ 0.124.0); trust it with `/hooks` |
| [Cursor](https://cursor.com/docs/rules) | Reads `AGENTS.md` natively. | Reads `.agents/skills/` natively. | `.cursor/hooks.json`, `.cursor/sandbox.json`, if you add them | [`sessionStart`](https://cursor.com/docs/hooks) in `.cursor/hooks.json` |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md) | Set `"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}` in `.gemini/settings.json`; it reads only `GEMINI.md` by default. | Reads `.agents/skills/` natively. | `.gemini/settings.json` | [`SessionStart`](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md) in `.gemini/settings.json` |
| [Copilot](https://docs.github.com/en/copilot/reference/custom-instructions-support) (CLI, VS Code) | Reads `AGENTS.md` natively. | Reads `.agents/skills/` natively. | `.github/copilot/settings.local.json` | [`sessionStart`](https://docs.github.com/en/copilot/reference/hooks-reference) in `.github/copilot/settings.local.json` |

Last checked: 2026-11-17.

### Agents on a machine account

To have agents act as a machine account with Write access, give the agent's environment that account's fine-grained token as `GH_TOKEN`, so `gh`, and `git` with `gh` as its credential helper, run as the account. Per provider:

- **Claude Code:** with the Bash sandbox on, add `api.github.com` and `github.com` to `sandbox.network.allowedDomains` in `.claude/settings.local.json`: `gh` calls the API, and `git fetch` and `git push` go to `github.com`.
- **Codex:** the sandbox has no network by default, so set `sandbox_workspace_write.network_access = true` in `.codex/config.toml`, which Codex loads only in a trusted project. A `shell_environment_policy` that narrows `inherit` or sets `include_only` must keep `GH_TOKEN`.
- **Cursor:** with the sandbox on, add `api.github.com` and `github.com` to `networkPolicy.allow` in `.cursor/sandbox.json`.
- **Gemini CLI:** if environment variable redaction is on, allowlist `GH_TOKEN`, because redaction strips names containing `TOKEN`.
- **Copilot:** Copilot signs itself in with `GH_TOKEN` ahead of a `copilot login` session, so it runs as the machine account, which then needs a Copilot seat. Setting `COPILOT_GITHUB_TOKEN` to your own token instead keeps Copilot on your account, but every command the agent runs inherits that token and can act as you.

### Accelerators

Each developer installs [Accelerators](GLOSSARY.md#workflow) through their provider's plugin mechanism. They stay out of the repo and out of `.agents/skills/`, so nothing the repo carries depends on one.
