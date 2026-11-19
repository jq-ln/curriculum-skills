# Wiki-link tooling for plain Markdown in LazyVim

Research for [#4](https://github.com/jq-ln/curriculum-skills/issues/4). Checked 2026-11-18.

## Recommendation

Use plain relative Markdown links with the `.md` extension, such as `[GIT 1.1.1 Snapshots](GIT-1.1.1-snapshots.md)` or `[…](../1.1-what-git-is/1.1.1-snapshots.md)`. Do not use `[[wiki links]]`.

- GitHub resolves relative links against the linking file, and an agent can open the target path directly. GitHub does not resolve `[[…]]` in repository files.
- In nvim, enable LazyVim's `lang.markdown` extra. It installs marksman, which resolves relative Markdown links with go-to-definition, references, completion and broken-link diagnostics. Nothing else needs installing.
- The skill writes a `.marksman.toml` (it may be empty) at the Curriculum root. A Curriculum directory may not be a git repo, and without `.git` or `.marksman.toml` marksman falls back to single-file mode with no cross-file features.

Naming rule: make every filename unique across the whole Curriculum and free of spaces, by putting the full ID in it (such as `GIT-1.1.1-snapshots.md`). Paths stay the real link target, but unique names mean any tool that matches by bare filename (markdown-oxide, zk's wiki fallback, obsidian.nvim's shortest form, marksman's wiki-link resolution) gets exactly one hit, and an agent can find a file by ID with one glob. No spaces means links need no `%20` or `<…>` escaping.

A flat layout (all files in one directory) is the one layout where `[text](name.md)` resolves in all four tools below. With subdirectories, markdown-oxide does not resolve `../` links (see its section). That is an input to #8, not a reason on its own to go flat, because marksman, zk and GitHub handle nested relative links.

## Summary table

| | marksman 2026-02-08 | markdown-oxide v0.25.12 | obsidian.nvim v3.16.10 | zk v0.15.7 / zk-nvim v0.5.4 |
| --- | --- | --- | --- | --- |
| In LazyVim today | Yes, via `lang.markdown` extra | No | No | No |
| `[[name]]` | Yes (title slug or file stem) | Yes (file stem) | Yes | Yes (path, then substring) |
| `[[path/name]]` | Yes (path match) | Yes, root-relative only | Yes | Yes |
| `[[name#heading]]` | Yes | Yes | Yes | Yes |
| `[[name\|alias]]` | Yes (parser) | Yes | Yes | Yes |
| `[text](path.md)` | Yes, file-relative or root-absolute | Bare name or root-relative path only; `../` fails | Yes | Yes, file-relative |
| Resolution | Title, path, or path suffix; ambiguity is a diagnostic | Bare name by filename; path by vault-root path | Configurable link format | Exact path first; wiki links fall back to fuzzy match |
| Go to definition | Yes | Yes | Yes | Yes |
| Backlinks / references | Yes | Yes | Yes | Yes (`:ZkBacklinks`) |
| Completion | Yes | Yes | Yes | Yes |
| Broken-link diagnostics | Yes | Yes | Not documented | Yes (`dead-link`) |
| Root marker | `.marksman.toml` or `.git` | `.git`, `.obsidian` or `.moxide.toml` | Workspace path in nvim config | `.zk/` directory (`zk init`) |

## LazyVim (v16.0.2)

- The installed LazyVim is v16.0.2 (released 2026-11-08). The user's `lazyvim.json` enables no markdown extra, so no markdown LSP runs today.
- The `lang.markdown` extra configures one LSP server, `marksman`, plus markdownlint-cli2, markdown-toc, markdown-preview.nvim and render-markdown.nvim. Enable it with `:LazyExtras`. Its docs do not mention wiki links, obsidian.nvim or markdown-oxide. Source: <https://www.lazyvim.org/extras/lang/markdown>, and the extra's source at <https://github.com/LazyVim/LazyVim/blob/v16.0.2/lua/lazyvim/plugins/extras/lang/markdown.lua>.
- LazyVim v16.0.2 ships no extra for obsidian.nvim, zk or markdown-oxide (only `extras/lang/markdown.lua` matches). Source: <https://github.com/LazyVim/LazyVim/tree/v16.0.2/lua/lazyvim/plugins/extras>.

## marksman (release 2026-02-08)

Latest release is tagged `2026-02-08`; `main` is 17 commits ahead with performance and diagnostics refactors only. Source: <https://github.com/artempyanykh/marksman/releases>.

- Link forms. Inline links (`[x](/some-file.md#some-heading)`, `[x](#heading)`), reference links, and wiki links (`[[another-note]]`, `[[another-notes#heading]]`, `[[#a-heading]]`). "All types of links support completion, hover, goto definition/references." Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/README.md>.
- `[[name|alias]]`. Not in the docs, but the wiki-link parser at this tag splits on an unescaped `|` into doc and title parts. Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Parser.fs>.
- Resolution. A wiki link resolves by the target's title (its level-1 heading, slugged) or by filename; `completion.wiki.style` (`title-slug` default, `file-stem`, `file-path-stem`) picks which form completion inserts and which binding wins on rename. Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/docs/features.md>, <https://github.com/artempyanykh/marksman/blob/2026-02-08/Tests/default.marksman.toml>. A wiki link containing a path matches documents whose path contains it, so `[[dir/name]]` works. Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Refs.fs>. Inline links resolve relative to the linking file, or from the root when they start with `/`. Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Names.fs>.
- Uniqueness. Names need not be unique, but a link that matches more than one document gets an "Ambiguous link" diagnostic. Source: <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Diag.fs>.
- Diagnostics. The README says diagnostics cover wiki links ("broken references and duplicate/ambiguous headings"). The source at this tag also reports broken inline links whose target looks like a Markdown file; inline shortcut links are exempt. Source: README above and `Marksman/Diag.fs` above.
- Completion of inline links inserts a root-absolute, URL-encoded path such as `/dir/file.md`, not a file-relative one. Source: `inlineDoc` in <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Compl.fs> and `AbsPathUrlEncode` in <https://github.com/artempyanykh/marksman/blob/2026-02-08/Marksman/Misc.fs>. A Curriculum should still use relative links (a leading `/` means the repo root on GitHub and the filesystem root to a naive reader), so the human edits the completed path or types it. The format's validator can flag `/`-rooted links.
- Root. A project root is a VCS root or a folder with `.marksman.toml`; without one, marksman runs in single-file mode and "cross-file references and completions don't work". Source: README and `docs/features.md` above. nvim-lspconfig's config uses `root_markers = { '.marksman.toml', '.git' }`. Source: <https://github.com/neovim/nvim-lspconfig/blob/master/lsp/marksman.lua>.
- Other: rename refactor, a "create missing linked file" code action, TOC code action. Source: `docs/features.md` and `Tests/default.marksman.toml` above.

## markdown-oxide (v0.25.12)

Released 2026-06-29. Source: <https://github.com/Feel-ix-343/markdown-oxide/releases>. Its docs note the configuration page reflects `main` and may list settings not in a release. Source: <https://github.com/Feel-ix-343/markdown-oxide/blob/main/docs/Markdown%20Oxide%20Docs/Configuration.md>.

- Features. Wikilink and Markdown-link completion to files and headings, file and heading references (backlinks), hover with backlinks, an "unresolved reference" diagnostic, rename of files and headings, and create-file code actions. Source: <https://github.com/Feel-ix-343/markdown-oxide/blob/main/docs/Markdown%20Oxide%20Docs/Features%20Index.md>.
- Link forms. The parser at v0.25.12 accepts `[[path#heading|display]]` (each part optional, optional `.md`) and `[display](path.md#heading)`. Source: `WIKI_LINK_RE` and `MD_LINK_RE` in <https://github.com/Feel-ix-343/markdown-oxide/blob/v0.25.12/src/vault/mod.rs>.
- Resolution. A link with no `/` matches any file whose stem equals it, case-insensitively, so bare names must be unique. A link containing `/` is compared with the target's path relative to the vault root (a leading `./` or `/` is stripped). Links are not resolved relative to the linking file, so `[x](../other/note.md)` does not resolve. Source: `matches_path_or_file` and `get_obsidian_ref_path` in `src/vault/mod.rs` above.
- Config. `~/.config/moxide/settings.toml` or `.moxide.toml`; `unresolved_diagnostics = true` by default; `include_md_extension_md_link = false` by default, so completion writes `[File](file)` without `.md` unless changed. Source: Configuration page above.
- Root. nvim-lspconfig uses `root_markers = { '.git', '.obsidian', '.moxide.toml' }`. Source: <https://github.com/neovim/nvim-lspconfig/blob/master/lsp/markdown_oxide.lua>; the README's manual config repeats it. Source: <https://github.com/Feel-ix-343/markdown-oxide/blob/v0.25.12/README.md>.

## obsidian.nvim (v3.16.10, community fork)

Released 2026-10-28. This is `obsidian-nvim/obsidian.nvim`, the community fork of `epwalsh/obsidian.nvim`. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/README.md>.

- Features. In-process LSP with completion on `[[`, follow link, backlinks (`:Obsidian backlinks`, `grr`), rename with backlink updates, plus Obsidian-style notes, templates and dailies. Source: README above.
- Link forms. Go-to-definition handles `[markdown note](markdown%20note.md)` and `[[wiki note]]`. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/docs/LSP.md>. Generated links follow `link.style` (`wiki` or `markdown`) and `link.format` (`shortest`, the default; `relative` to the current note; or `absolute` from the vault root). The default wiki form is `[[basename|Label]]`. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/docs/Link.md>.
- Diagnostics. The docs at this tag describe no broken-link diagnostic; unresolved links prompt to create the note when followed. Source: README above.
- Workspace. Requires `workspaces` in the nvim config, each a vault path; a "dynamic" workspace whose path is a function can cover directories outside fixed vaults. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/docs/Workspace.md>.
- Note IDs default to random zettel IDs, with a title-based preset; the docs say 4.0.0 will default to title-based. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/docs/Note.md>. It reads `id` and `aliases` from frontmatter. Source: <https://github.com/obsidian-nvim/obsidian.nvim/blob/v3.16.10/docs/Frontmatter.md>.
- Fit: it is built around Obsidian vaults and its own note conventions, which is more than a generated Curriculum needs.

## zk (v0.15.7) and zk-nvim (v0.5.4)

zk v0.15.7 released 2026-10-15; zk-nvim v0.5.4 released 2026-11-18. Sources: <https://github.com/zk-org/zk/releases>, <https://github.com/zk-org/zk-nvim/releases>.

- Features. The `zk lsp` server completes links on `[[`, previews on hover, follows internal links, and reports dead links, wiki-link titles and missing backlinks. Source: <https://github.com/zk-org/zk/blob/v0.15.7/docs/tips/editors-integration.md>. `dead-link` defaults to `error`. Source: <https://github.com/zk-org/zk/blob/v0.15.7/docs/config/config-lsp.md>. zk-nvim adds `:ZkBacklinks` and `:ZkLinks` pickers. Source: <https://github.com/zk-org/zk-nvim/blob/v0.5.4/README.md>.
- Link forms. Generated links are Markdown by default; `link-format` can be `wiki` or a template such as `[[{{metadata.id}}|{{title}}]]`; `link-drop-extension` defaults to `true`. Source: <https://github.com/zk-org/zk/blob/v0.15.7/docs/notes/note-format.md>.
- Resolution. Markdown and wiki links resolve relative to the linking file's directory, or from the notebook root when they start with `/`. If that fails, a wiki link falls back to a filename substring match, then a path substring match, and takes the first hit. Source: `noteForLink` and `noteForHref` in <https://github.com/zk-org/zk/blob/v0.15.7/internal/adapter/lsp/server.go>, `FindIdsByHref` in <https://github.com/zk-org/zk/blob/v0.15.7/internal/adapter/sqlite/note_dao.go>. Notes are identified by path relative to the notebook root. Source: <https://github.com/zk-org/zk/blob/v0.15.7/docs/notes/note-id.md>.
- Root. A notebook is a directory with a `.zk/` directory (`config.toml`, templates and a `notebook.db` SQLite index), made with `zk init`. Source: <https://github.com/zk-org/zk/blob/v0.15.7/docs/notes/notebook.md>. nvim-lspconfig uses `root_markers = { '.zk' }`. Source: <https://github.com/neovim/nvim-lspconfig/blob/master/lsp/zk.lua>.
- Fit: it would add a `.zk/` directory with a database to every Curriculum.

## How GitHub and agents read the same links

- GitHub: "A relative link is a link that is relative to the current file", and "Links starting with `/` will be relative to the repository root." The page describes no `[[…]]` syntax for repository files. Source: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes#relative-links-and-image-paths-in-markdown-files>. The GFM spec defines inline and reference links and has no wiki-link extension. Source: <https://github.github.com/gfm/>. So `[[name]]` shows as literal bracketed text on GitHub.
- Agents read raw files. A relative path with `.md` can be opened as-is from the linking file's directory. A `[[name]]` link needs a search for the file, and an extension-less link (oxide's and zk's default when they generate links) needs the agent to guess `.md`. This point is reasoning from the formats, not from a cited source.
