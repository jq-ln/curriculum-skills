# Packaging and local install for shipped skills

Research for [#10](https://github.com/jq-ln/curriculum-skills/issues/10), under the map [#2](https://github.com/jq-ln/curriculum-skills/issues/2). Sources checked 2026-11-18 against Claude Code 2.1.327. The working example is `mattpocock-skills` 1.3.1 at `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.3.1/`; its file paths below are relative to that directory.

## Recommendation

Put a copy of `docs/curriculum-format.md` inside each skill that needs it, as `skills/<name>/references/curriculum-format.md`, and have `SKILL.md` link it by a path relative to the skill directory: `[the format](references/curriculum-format.md)`. Keep `docs/curriculum-format.md` as the one file humans edit, and make the copies with a sync script that CI checks, so the copies can't drift.

Don't reference the doc through `${CLAUDE_PLUGIN_ROOT}` or through `../../docs/`. Both work only in some installs:

- `${CLAUDE_PLUGIN_ROOT}` is substituted in skill content only by Claude Code, and only for plugin skills. Codex, Copilot, Cursor, Gemini CLI and the Agent Plugins spec substitute their plugin-root variables in hooks or MCP config, not in skills.
- A path that leaves the skill directory breaks under every installer that copies one skill folder, such as `gemini skills install --path`, and under Gemini CLI's access rule, which grants the agent the skill's own directory.

The skill directory is the only unit every agent and every install route is documented to keep together. The Agent Skills spec says to reference other files "using relative paths from the skill root" ([Agent Skills spec, File references](https://agentskills.io/specification#file-references)).

For packaging, ship the repo root as one plugin, the way `mattpocock-skills` does, with skills in a flat `skills/<name>/SKILL.md` layout. For local testing, `claude --plugin-dir <clone>` is the minimum in Claude Code; for every agent at once, symlink each `skills/<name>` into `~/.agents/skills/` and `~/.claude/skills/`.

## How a skill references a repo-level doc

### Options compared

| Option | Claude Code plugin | Claude Code personal skill | Codex, Copilot, Cursor | Gemini CLI |
| --- | --- | --- | --- | --- |
| Copy inside the skill, relative link | Works | Works | Works | Works |
| Symlink inside the skill to `../../docs/…` | Works when the plugin root is the repo root (symlink target stays inside the plugin) | Works if the agent resolves the symlink | Undocumented for installs; Cursor local plugins reject symlinks that leave the folder | Undocumented for `skills install` |
| `${CLAUDE_PLUGIN_ROOT}/docs/curriculum-format.md` | Works | Not substituted | Not substituted | Not substituted |
| `../../docs/curriculum-format.md` | Works only while the whole repo is the plugin root | Breaks if the skill is copied or symlinked alone | Breaks under per-skill installers | Outside the directory Gemini grants |
| Separate model-invoked `curriculum-format` skill that other skills load | Works | Works | Works | Works |

The last row keeps one copy, but each producer skill then depends on the agent loading a second skill by name, and in Claude Code a plugin skill's name carries the plugin prefix (`/plugin-name:skill-name`, [skills](https://code.claude.com/docs/en/skills)). `mattpocock-skills` describes this pattern for reference several skills share (`skills/productivity/writing-for-agents/SKILL-MECHANICS.md` in the cached 1.3.1 plugin). It's the fallback if a copy per skill becomes a burden.

### Evidence, by agent

**Claude Code.**

- Skill content can use `${CLAUDE_SKILL_DIR}` (the skill's directory), `${CLAUDE_PROJECT_DIR}`, and, "substituted only in plugin skills", `${CLAUDE_PLUGIN_ROOT}` ([skills, string substitutions](https://code.claude.com/docs/en/skills)).
- A marketplace plugin is copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and "Files outside the plugin directory aren't copied, so when a script inside a copied plugin reads a path above the plugin root, such as `../shared`, it doesn't find them" ([plugin loading, In-place and copied plugins](https://code.claude.com/docs/en/plugins/loading)).
- Symlinks inside a plugin survive the copy when the target is inside the plugin; a target elsewhere in the marketplace is dereferenced; a target outside it is skipped. For plugins installed from a local path, only symlinks inside the plugin's own directory are kept ([host a marketplace, Share files within a marketplace with symlinks](https://code.claude.com/docs/en/plugins/host-marketplace)).
- `${CLAUDE_PLUGIN_ROOT}` points at a version directory and changes with every update ([plugin loading, Find plugins on disk](https://code.claude.com/docs/en/plugins/loading)). That's fine for reading a doc, not for writing state.
- Consequence: with the repo root as plugin root, `docs/` is inside the plugin and is copied, so `${CLAUDE_PLUGIN_ROOT}/docs/curriculum-format.md` resolves in Claude Code. It stops resolving the moment the same skill is installed as a personal skill or by any other agent.

**Codex.** Plugin hook commands receive `PLUGIN_ROOT` and `PLUGIN_DATA`, and "Codex also sets `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility with existing plugin hooks". The page doesn't describe substitution in skills ([Package your plugin](https://developers.openai.com/codex/plugins/build)). Codex's skills page lists `scripts/`, `references/` and `assets/` inside the skill and says nothing about files outside it ([Build skills](https://learn.chatgpt.com/docs/build-skills)).

**Copilot CLI.** `${PLUGIN_ROOT}` (aliases `${CLAUDE_PLUGIN_ROOT}`, `${COPILOT_PLUGIN_ROOT}`) expands in MCP server `args`, `env` and `cwd`, LSP `cwd`, and agent frontmatter `mcp-servers`. The reference doesn't describe it in skills ([CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)).

**Cursor.** The plugins page documents `${CURSOR_PLUGIN_ROOT}` for `mcp.json` only ([Plugins](https://cursor.com/docs/plugins)). The skills page documents only paths relative to the skill root ([Skills](https://cursor.com/docs/skills)).

**Gemini CLI.** `${extensionPath}` is substituted "in `gemini-extension.json` and `hooks/hooks.json`" ([extension reference](https://geminicli.com/docs/extensions/reference/)). On activation, "the skill's directory is added to the agent's allowed file paths so it can read bundled assets" ([Skills](https://geminicli.com/docs/cli/skills/)), so a file outside the skill directory may not be readable.

**Agent Plugins 1.0** (the cross-vendor format Codex, Cursor, Copilot and VS Code adopted): `${PLUGIN_ROOT}` expands only in MCP stdio `args`, `env` and `cwd`, and the spec defines no plugin-root variable for skills. Package paths and symlinks must resolve inside the plugin root ([spec §4.1, §9.2](https://agent-plugins.org/specification)).

**The working example.** No skill in `mattpocock-skills` 1.3.1 links a file outside its own directory. Every cross-file link is a sibling, such as `[LOGIC.md](LOGIC.md)` in `skills/engineering/prototype/SKILL.md`, and the plugin has no symlinks under `skills/`. Mentions of `docs/adr/` in `domain-modeling` refer to the user's project, not to the plugin. The repo's own `docs/` holds website pages, not files a skill reads.

### Keeping the copies in sync

Two ways, both inside the repo's control:

- **Committed copy plus a CI check** (recommended): a script copies `docs/curriculum-format.md` into every `skills/*/references/` that declares it, and the `ci` job fails when a copy differs. The copy is a regular file, so every installer carries it.
- **Committed symlink** `skills/<name>/references/curriculum-format.md -> ../../../docs/curriculum-format.md`: no sync step, and it survives Claude Code's marketplace copy because the target is inside the plugin root. It's unverified for Codex, Copilot and Gemini installs, and Cursor's local-plugin loader accepts a symlink only if "the target resolves to a directory inside that folder" ([Plugins](https://cursor.com/docs/plugins)). Use it only if Claude Code is the sole supported agent.

## Packaging

### The working example

`mattpocock-skills` 1.3.1 ships the whole repo as one plugin:

- `.claude-plugin/marketplace.json` names the marketplace (`mattpocock`) and lists one plugin with `"source": "./"`, so the plugin root is the repo root.
- `.claude-plugin/plugin.json` sets `name`, `version`, and a `skills` array of the promoted skill directories, because its skills sit in buckets (`skills/engineering/<name>/`) rather than directly under `skills/`.
- Its install doc (`.agents/install-block.md`) installs the same repo into Codex (`codex plugin marketplace add mattpocock/skills`), Copilot CLI (`copilot plugin marketplace add mattpocock/skills`) and VS Code (Chat: Install Plugin From Source), and notes that a Gemini extension "would need a flat `skills/<name>/` layout", so Gemini users run `gemini skills install … --path skills/<bucket>` instead.
- `scripts/link-skills.sh` is its maintainer-only local install: it symlinks every skill directory into `~/.claude/skills` and `~/.agents/skills`, so a `git pull` updates them.

### Layout for this repo

```text
curriculum-skills/
├── .claude-plugin/
│   ├── plugin.json        # name, version; no skills key needed with a flat skills/
│   └── marketplace.json   # one entry, "source": "./"
├── skills/
│   └── <name>/
│       ├── SKILL.md
│       └── references/
│           └── curriculum-format.md   # synced copy of docs/curriculum-format.md
├── docs/curriculum-format.md          # the one file humans edit
└── .agents/skills/                    # skills for working on this repo; not shipped
```

Why each piece:

- **Flat `skills/<name>/SKILL.md`.** Claude Code scans `skills/` by default ([manifest reference, Standard layout](https://code.claude.com/docs/en/plugins/manifest-reference)). Agent Plugins fixes skills at `skills/` and the manifest can't move them ([spec §6.1](https://agent-plugins.org/specification)). Gemini extensions also read `skills/` ([extension reference](https://geminicli.com/docs/extensions/reference/)). A flat layout avoids the bucket problem `mattpocock-skills` has with Gemini.
- **`.claude-plugin/plugin.json` and `marketplace.json`.** Claude Code reads the manifest only at `.claude-plugin/plugin.json` ([manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference)). Copilot CLI checks `.claude-plugin/plugin.json` among its legacy locations and also looks for `marketplace.json` in `.claude-plugin/` ([CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)). Codex accepts "a legacy-compatible marketplace at `$REPO_ROOT/.claude-plugin/marketplace.json`" and "legacy and Claude-compatible manifests" ([Package your plugin](https://developers.openai.com/codex/plugins/build)).
- **`.agents/skills/` stays unshipped.** Claude Code scans only `skills/` and paths the manifest lists, so `.agents/skills/` isn't loaded from the plugin. It's still inside the copied plugin root, which costs disk space and nothing else.
- **`version`.** Setting `version` in `plugin.json` pins users to it until it changes; omitting it makes Claude Code track the commit SHA ([plugin loading, Versions and updates](https://code.claude.com/docs/en/plugins/loading)). This repo already has release-please and `version.txt`, so the Spec should decide whether release-please also writes `plugin.json`'s `version`, as `mattpocock-skills` does with `sync-plugin-version.mjs`.

Optional, decided by the Spec: a root `plugin.json` with `"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"` and `name` makes the repo an Agent Plugins 1.0 package for Codex, Cursor and Copilot ([spec §5.2–5.3](https://agent-plugins.org/specification)). Copilot gives a root Agent Plugins manifest precedence over `.claude-plugin/` ([CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)). Claude Code's docs don't mention a root `plugin.json`, so check `claude plugin validate .` with one present before relying on it. A Gemini extension needs its own `gemini-extension.json` at the root.

## Minimum local install for testing

Each route loads the working tree in place, so edits show up without a release.

| Agent | Command | Picks up edits |
| --- | --- | --- |
| Claude Code, one session | `claude --plugin-dir /path/to/curriculum-skills` | Run `/reload-plugins` ([create a plugin](https://code.claude.com/docs/en/plugins/create)) |
| Claude Code, every session | `claude plugin marketplace add /path/to/curriculum-skills`, then `claude plugin install <plugin>@<marketplace>` | At next session start or `/reload-plugins`; a relative-path plugin in a local marketplace "loads in place" and ignores `version` ([plugin loading](https://code.claude.com/docs/en/plugins/loading)) |
| Copilot CLI | `copilot plugin marketplace add /path/to/curriculum-skills`, then `copilot plugin install <plugin>@<marketplace>` | Path-sourced plugins in a local directory marketplace "load live from their real directory" ([CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)) |
| Codex | `codex plugin marketplace add /path/to/curriculum-skills` | Docs say to test local plugins in the ChatGPT desktop app, which installs to `~/.codex/plugins/cache/<marketplace>/<plugin>/local/`; restart after edits ([Package your plugin](https://developers.openai.com/codex/plugins/build)) |
| Gemini CLI | `/skills link /path/to/curriculum-skills/skills` in a session | Links rather than copies ([Skills](https://geminicli.com/docs/cli/skills/)) |
| Cursor | Plugin in `~/.cursor/plugins/local`, then Developer: Reload Window | A symlink there loads only if its target is inside that folder, so copy or use the next row ([Plugins](https://cursor.com/docs/plugins)) |

The one route that covers every agent is the `mattpocock-skills` approach: symlink each `skills/<name>` into `~/.agents/skills/<name>` and `~/.claude/skills/<name>`. Codex, Cursor, Gemini CLI and Copilot read `~/.agents/skills/` ([Build skills](https://learn.chatgpt.com/docs/build-skills), [Cursor Skills](https://cursor.com/docs/skills), [Gemini Skills](https://geminicli.com/docs/cli/skills/), [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)); Claude Code reads only `~/.claude/skills/`. Claude Code and Codex document following skill symlinks and watching for changes ([skills](https://code.claude.com/docs/en/skills), [Build skills](https://learn.chatgpt.com/docs/build-skills)); the other three don't say. This route installs skills as personal skills, not a plugin, so it works only if each skill directory is self-contained, which the recommendation above guarantees.

## Open points for the Spec

- Whether release-please writes `version` into `.claude-plugin/plugin.json`, or the manifest omits `version` and users track commits.
- Whether to add a root Agent Plugins `plugin.json` and a `gemini-extension.json`, or leave Codex, Copilot and Gemini on the `.claude-plugin/` compatibility path and per-skill installs.
- The README's provider table: Gemini CLI was replaced by Antigravity CLI on 2026-06-18 for unpaid-tier and Google One users ([extension reference](https://geminicli.com/docs/extensions/reference/)).
- Unverified here: whether Codex, Copilot and Gemini installers preserve a symlink inside a skill. Only matters if the Spec picks the symlink option.
