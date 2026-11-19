# Curricula inventory: fields, front matter, back matter and tags

Research for #3. Sources: the 9 Markdown files in `~/Documents/curriculum/`, read directly on 2026-11-18. Citations are `file:line`. Every count below was taken with `grep`/`awk` over the files, not estimated.

## Summary

The 9 files fall into four formats, not one:

1. **Rich per-session blocks, chaptered** (5 files): `data-structures-and-algorithms.md`, `game-design.md`, `git.md`, `postgresql.md`, `javascript.md`. Part › Chapter › Session, a 7-row field table (Goal, Scope, Key concepts, Foundations, Prereqs, Check, Sources), a chapter-level `> **Click:**` line, a tag legend, and a "Notes and open questions" back matter with the same four subsection types. These five are near-copies of one template, but the template drifted: the field legends differ in three rows and the tag schemes share almost nothing.
2. **Rich per-session blocks, flat** (1 file): `command-line-mastery.md`. Part › Session, sessions numbered 1–134 globally. Its fields are a different set (Goal, Generators, Foundation, Scope, Prereqs, Sources, Shells): no Key concepts and no Check, a per-session Generators field instead of a chapter Click line, singular `Foundation` placed before Scope, and a per-Part sources line. No tag scheme, no Notes; it has two appendices instead.
3. **One-line sessions** (2 files): `math.md` and `system-design.md`. Part › Chapter › Session with a `P.C.S` ID, each session a single bullet line. Math has no labelled Goal at all (title + description + optional `*Needs:*`); system design has `**Goal:**`, optional `**Prereq:**` and `**Src:**` inline. Neither has Check, Key concepts or Foundations fields. Sources are attached to chapters (math) or sessions (system design); prerequisites can be attached to the Part (system design).
4. **A schedule that points into the other maps** (1 file): `interview-fast-track.md`. Weeks of tables whose cells are pointers like `DSA 64.3` or `SD 22.7.4`, plus 19 new sessions in the rich format minus Foundations.

Things that will make a single standard doc set or field set harder:

- **The same `[…]` syntax means three different things.** In five files it is a status/kind tag on a heading (`[Synthesis]`, `[PG19]`, `[ES2022]`). In `command-line-mastery.md` and `math.md` it is a source abbreviation (`[BASH] §3.1.1`, `[OS-Calc1] §4.4`). `javascript.md` also uses free-form bracket text that is not in its own legend (`[advanced]`, `[incl. ES2025/ES2026]`, `[mostly Non-normative]`).
- **"Synthesis/click" is marked five ways**: `[Synthesis]` tag (DSA, GD, git, PG), `(click session)` in the title (JS, ITF), `(synthesis)` in a pointer title (ITF), a `**Goal:** Synthesis:` prefix (SD, 10 sessions), and nothing at all (math, CLM).
- **Generators live at three levels**: a chapter `> **Click:**` line (5 files), a per-session `**Generators:**` field on 16 of 134 sessions (CLM), or only in prose (math, SD).
- **Prerequisite semantics differ.** Five files list *all direct* prereqs, backward only. Math and SD list only prereqs *other than the previous session* (`Needs:`, `Prereq:`), and SD adds Part-level prereqs. ITF prereqs point into other files and carry `(preview)`/`(assumed)` qualifiers. CLM has two forward references in Prereqs (sessions 86 and 112).
- **Tags attach at different levels.** Legends describe session tags, but `game-design.md` puts `[Math]` only on chapters (23–26) and `[Regulation]` on Chapter 52; `postgresql.md` tags Chapter 40 `[PG18]`; `javascript.md` tags its appendices.
- **Three files have no tag legend and two have no per-session field legend table**, so any standard field set has to be inferred for them from prose (`command-line-mastery.md:9-19`, `math.md:31-36`, `system-design.md:9-13,35-36`, `interview-fast-track.md:111`).

## Files at a glance

Short names used below: **CLM** `command-line-mastery.md`, **DSA** `data-structures-and-algorithms.md`, **GD** `game-design.md`, **git** `git.md`, **PG** `postgresql.md`, **JS** `javascript.md`, **math** `math.md`, **SD** `system-design.md`, **ITF** `interview-fast-track.md`.

| File | Lines | Sessions | Chapters | Parts | Unit heading form | Session ID |
|---|---:|---:|---:|---:|---|---|
| CLM | 1040 | 134 | — | 14 (I–XIV) | `### 1. Title` (H3) | global integer `1`–`134` |
| DSA | 3178 | 338 | 64 | 16 (I–XVI) | `#### 1.1 Title` (H4) | `Chapter.Session` |
| GD | 2105 | 199 | 56 | 19 (I–XIX) | `#### 1.1 Title` (H4) | `Chapter.Session` |
| git | 1970 | 192 | 52 | 19 (I–XIX) | `#### 1.1 Title` (H4) | `Chapter.Session` |
| PG | 2348 | 232 | 60 | 24 (I–XXIV) | `#### 1.1 Title` (H4) | `Chapter.Session` |
| JS | 1800 | 182 (169 core + 13 appendix) | 37 + 3 appendices | 18 (I–XVIII) | `#### 1.1 Title`; appendices `#### A.1 Title` (H4) | `Chapter.Session`, `A.n` |
| math | 1574 | 776 | 114 | 16 (1–16) | bullet `- **1.1.1 Title** — …` | `Part.Chapter.Session` |
| SD | 1285 | 586 | 127 | 22 (1–22) | bullet `- **1.1.1 Title** — **Goal:** …` | `Part.Chapter.Session` |
| ITF | 271 | 71 + 1 mock slot (19 defined in full) | — | 4 weeks | `#### TS 1 Title` (H4, no H3) | prefix + integer (`TS 1`, `RE 8`); pointers `JS 8.3`, `SD 22.7.4` |

Every stated count matches the actual count: DSA 338 (`data-structures-and-algorithms.md:5`), GD 199 (`game-design.md:5`), git 192 (`git.md:5`), PG 232 (`postgresql.md:5`), JS 182 (`javascript.md:5`), math 776 (`math.md:9`), SD 586 (`system-design.md:42`), CLM 134 (`command-line-mastery.md:994`). Tag counts stated in the summary bullets also match (DSA 10/14/8 `[Synthesis]`/`[Advanced]`/`[Overview]`; GD 19, git 16, PG 14 `[Synthesis]`).

## Element × file table

"—" means absent. Line numbers are the element's first line or its range.

### Front matter

| Element | CLM | DSA | GD | git | PG | JS | math | SD | ITF |
|---|---|---|---|---|---|---|---|---|---|
| H1 title | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Intro paragraph (what the map covers; "each numbered session is one session") | 3 | 3 | 3 | 3 | 3 | 3 | — (scope in 7–9) | — (scope in 7) | 3 |
| Pointer-prefix table (which map each ID prefix refers to) | — | — | — | — | — | — | — | — | 5–13 |
| `Sessions:` count line | — (count only in App. A, 976–994) | 5 | 5 | 5 | 5 | 5 | prose 9 | prose 42 | 17 |
| Snapshot / compile date | 5 (italic, with installed tool versions) | 6 `Snapshot:` | 6 `Snapshot:` | 6 `Snapshot:` | 6 `Snapshot:` | 6 `Snapshot date:` | 3 (italic) | 3 (italic) | — (no date anywhere) |
| Target version statement | 5 (bash 5.3.20 … iproute2 7.3.0) | — (editions in 6) | — ("no versions", 6) | 6 (Git 2.56) | 6 (PostgreSQL 18; PG19 RC2) | 6 (ES2027 editor's draft) | — | — | 111 (TS 5.x, React 19, Next.js 15/16) |
| Other summary bullets | — | 7 `Language-neutral.` | 7 `What "primary source" means here:` | 7 `How the version was established:`; 8 `Documentation links` | 7 `Documentation section numbers` | — | — | — | 18–30 (time budget, daily block table, Sunday plan) |
| Methodology section | 9–19 "How this map fits learnharness" (7 bullets) | 11–22 "How the teaching methodology shaped this map" (8 numbered) | 11–22 (same heading, 8) | 12–23 (same heading, 8) | 11–22 (same heading, 8) | 10–21 "…shaped this curriculum" (8) | 11–29 "How session size was chosen" (4 quotes + 5 bullets) | 5–13 "How to use this list" (bold-led paragraphs) | 32–39 "How the fast track differs from the full maps" (4) |
| Ordering rationale | 21–28 (6) | 24–33 (8) | 24–39 (8) | 25–37 (6) | 24–33 (4) | — (only back-matter "Ordering and granularity choices") | 60–72 "Parallel tracks" + 74–85 "Ordering decisions and source conflicts" (10) | 11 `**Ordering.**` paragraph | 35 (item 2, "Choosing by interview yield") |
| Per-session field legend | 9–19 (prose bullets inside methodology) | 35–47 table | 41–53 table | 39–51 table | 35–47 table | 23–33 table | 31–36 "How to read the numbering" | 9, 11, 35–36 (prose + "Format of a session line") | 111 (one prose sentence) |
| "Each chapter also opens with a Click line" note | — | 47 | 53 | 51 | 47 | — (only methodology item 4, 17) | — | — | — |
| Tag legend | — | 49–55 "Tags" | 55–63 "Tags" | 53–64 "Tags" | 49–57 "Tags" | 35–45 "Status tags" | 35–36 (source tags; "(optional)") | — | — |
| Source table / abbreviations | 30–45 "Source abbreviations" (Tag \| Source) | 57–77 "Sources" (Key \| Source \| How cited) | 65–119 "Sources": 69 "Book abbreviations" (Abbreviation \| Book \| Link \| ToC checked against), 107 "Other families" (Family \| Where \| How cited) | 66–81 "Sources" (Abbreviation in link text \| Family \| Where) | 59–75 "Sources" (Family \| Where \| How cited) | 47–60 "Sources" (bullet list) | — in front (back matter 1530–1574) | 13–33 inside `**Citations.**` (Key \| Source) | — |
| Outline table | — (App. A at back) | 79–101 (Part \| Title \| Chapters \| Sessions) | 121–145 (same) | 83–107 (same) | 77–106 (same) | — | 38–58 "Session counts" (same columns) | 40–65 bullet list "Part N — Title (n sessions)" | 15–30 "At a glance" + 41–89 weekly tables |
| H1 `# Table of contents` divider | — | 103 | 147 | 109 | 108 | 64 | — | — | `# Schedule` 41, `# Optional extensions` 93, `# New sessions` 109 |

### Unit (session) fields

Counts are sessions carrying the field / total sessions. Field order is fixed within each file; the order shown is the order in the file.

| Field | CLM (134) | DSA (338) | GD (199) | git (192) | PG (232) | JS (182) | math (776) | SD (586) | ITF new (19) |
|---|---|---|---|---|---|---|---|---|---|
| Goal | `**Goal:**` 134 | 338 | 199 | 192 | 232 | 182 | — (unlabelled description after `—`, 776) | `**Goal:**` 586 | 19 |
| Generators | `**Generators:**` 16 | — | — | — | — | — | — | — | — |
| Foundation(s) | `**Foundation:**` 4 (singular, placed after Goal) | `**Foundations:**` 18 | 5 | 6 | 15 | 5 | — | — | — |
| Scope | 134 | 338 | 199 | 192 | 232 | 182 | — | — | 19 |
| Key concepts | — | 338 | 199 | 192 | 232 | 182 | — | — | 19 |
| Prereqs | `**Prereqs:**` 134 | 338 | 199 | 192 | 232 | 182 | `*Needs:*` 375 (only non-adjacent prereqs) | `**Prereq:**` 286 (only extra prereqs) | 19 |
| Check | — | 338 | 199 | 192 | 232 | 182 | — | — | 19 |
| Sources | `**Sources:**` 134 | 338 | 199 | 192 | 232 | 182 | — (chapter level) | `**Src:**` 586 | 19 |
| Shells | `**Shells:**` 19 (last field) | — | — | — | — | — | — | — | — |

Field order per file:

- CLM: Goal, [Generators], [Foundation], Scope, Prereqs, Sources, [Shells]. Six combinations occur: 98 sessions have only the four always-present fields; 16 add Shells; 14 add Generators; 3 add Foundation; 2 add Generators and Shells; 1 adds Foundation and Shells. No session has both Generators and Foundation.
- DSA, GD, git, PG, JS: Goal, Scope, Key concepts, [Foundations], Prereqs, Check, Sources. No other line ever appears inside a session block in these files.
- ITF: Goal, Scope, Key concepts, Prereqs, Check, Sources (no Foundations on any of the 19).
- math: `- **P.C.S Title** — description. *Needs: P.C.S Title; …*` (example `math.md:125`).
- SD: `- **P.C.S Title** — **Goal:** … · **Prereq:** … · **Src:** …` (example `system-design.md:81`).

Value conventions inside fields:

- **Empty Prereqs**: `none` in CLM (`command-line-mastery.md:57`) and ITF (`interview-fast-track.md:119`); `—` in DSA (116, 191), GD (160), git (122), PG (121), JS (77). Math and SD omit the field.
- **Qualified Prereqs**: CLM `85 (submitting additionally needs 114)` (`command-line-mastery.md:645`, session 86) and `5, 109 (the -e ssh/scp/sftp parts assume 113–114; …)` (`command-line-mastery.md:821`, session 112). Both point forward, against the backward-only rule the five chaptered files state. ITF `JS 27.2 (preview)` (185), `SD 5.3.3 (preview)` (243), `SD 2.5.3 (assumed)` (269).
- **Cross-map references**: ITF Prereqs point into other files by prefix (`JS 8.3`, `SD 2.5.3`). GD cites math sessions inside **Sources**, not Prereqs, as `` `math.md` 12.1.4 `` (`game-design.md:950`, `966`); its `[Math]` legend says the learner "should take the cited sessions in `math.md` first" (`game-design.md:61`).
- **Sources form**: abbreviation keys (CLM `[BASH] §3.1.1`, DSA `CLRS ch. 2`, GD `HL ch. I "…"`, SD `DDIA1 ch. 1`), full Markdown links (git, PG, JS, ITF), or mixed (GD papers and talks are linked inline).
- **Goal phrasing**: the five chaptered files, CLM and ITF phrase Goal as a proposition ("A commit stores…"). SD mostly phrases it as a learner action: of 586 Goals, 283 start "Understand", 81 "See", 41 "Know", 25 "Design"; 10 start "Synthesis:" and 1 "Internalise:".

### Grouping-level fields (attached to a Part, chapter or appendix)

| Element | CLM | DSA | GD | git | PG | JS | math | SD | ITF |
|---|---|---|---|---|---|---|---|---|---|
| Part heading | `## Part I — Title` | `## Part I — Title` | same | same | same | same | `## Part 1 — Title` | `## Part 1 — Title` | `## Week 1: …` |
| Part-level sources line | 14/14: `*Sources for the part: …*` (51, 153) or `*Sources: …*` (343 … 948) | — | — | — | — | — | 16/16: `*Sources: …* · **N sessions**` (90) | — | — |
| Part-level prose (ordering/placement note) | — | — | — | — | — | — | 16/16 one paragraph (92, 155, 301, 429, 539, 610, 654, 820, 938, 1030, 1108, 1192, 1270, 1349, 1437, 1496) | 2 (inside the italic line: 696, 995) | — |
| Part-level prerequisites | — | — | — | — | — | — | — | 21/22 `*Prereq for the Part: …*` (133 … 995); Part 1 has `*Assumed before Part 1: …*` (70) | — |
| Chapter heading | — | `### Chapter 1 · Title` | same | same | same | same | `### 1.1 Title` | `### 1.1 Title` | — |
| Chapter `> **Click:**` line | — | 64/64 | 56/56 | 52/52 | 60/60 | 36/37 (Chapter 37 at 1613 has none) | — | — | — |
| Chapter-level sources line | — | — | — | — | — | — | 114/114 `*Sources: …*` (96) | — | — |
| Chapter-level prerequisites | — | — | — | — | — | — | — | 0 (though 11 says sessions may depend on "the chapter's stated prerequisites") | — |
| Appendix-level Click | — | — | — | — | — | Appendix A 1647, B 1699; C none | — | — | — |
| Appendix intro prose | — | — | — | — | — | 1643 (under H1 `# Optional appendices: hosts and practice`, 1641) | — | — | — |
| Tag on a grouping heading | — | — | `[Math]` Ch. 23–26 (924, 968, 996, 1024); `[Regulation]` Ch. 52 (1888) | — | `[PG18]` Ch. 40 (1570) | `[Host: HTML / DOM]` App. A (1645), `[Host: Node]` App. B (1697), `[Non-normative]` App. C (1733) | `(optional)` Ch. 11.6 (1180) | — | — |

### Back matter

| Element | CLM | DSA | GD | git | PG | JS | math | SD | ITF |
|---|---|---|---|---|---|---|---|---|---|
| Appendices with sessions | — | — | — | — | — | 1641–1759: A browser host (6), B Node host (4), C tooling (3) | — | — | — |
| Count appendix | App. A "Session count by part" 976–994 | — | — | — | — | — | — | — | — |
| Coverage appendix | App. B "Coverage cross-check against the manuals' own structure" 996–1009 | in Build notes 3178 | — | in Build notes 1970 | in Build notes 2348 | — | — | — | — |
| `# Notes and open questions` | — | 3147 | 2046 | 1937 | 2317 | 1761 | — | — | — |
| › status / judgement calls | — | 3149 "Source status: judgement calls" | 2048 "Claims whose originator could not be traced"; 2056 "Citations that could not be fully verified"; 2083 "Regulation: dates and judgement calls `[Regulation]`" | 1939 "Version status: judgement calls" | 2319 "Version status: judgement calls" | 1763 "Standardisation status: judgement calls" | — | — | — |
| › Scope decisions | — | 3159 | 2089 | 1949 | 2327 | 1777 | — | — | — |
| › Ordering and granularity choices (incl. split/merge candidates) | — | 3166 (split 3172) | 2095 (split 2099) | 1955 (split 1962) | 2334 (split 2340) | 1788 (split 1794, merge 1795) | — | — | — |
| › Build notes (for whoever maintains this file) | — | 3174 | 2101 | 1964 | 2342 | 1797 | — | — | — |
| Notes numbering | — | 1–19, continuous across subsections | 1–21 | 1–21 | 1–19 | 1–19 | — | — | — |
| Trailing `## Sources` | 1011–1040 (grouped by family; `*Note on access:*` 1040) | — (front) | — (front) | — (front) | — (front) | — (front) | 1530–1574: "Standards and course frameworks" 1534, "OpenStax textbooks" 1544, "MIT OpenCourseWare" 1556, "Sources tried but not used, or not consulted" 1569 | 1125–1285: "How citations were verified" 1127, "Books" 1134, "Courses" 1149, "Papers (by topic)" 1156, "Specifications" 1269, "Official documentation and engineering references" 1277 | — |
| Plan extensions | — | — | — | — | — | — | — | — | `# Optional extensions` 93–107 (senior loops, early interview, after the month) |

## Tags

### Heading tags (status or kind)

Counts are headings carrying the tag (session headings unless noted). Tags are backticked and follow the title, several per heading allowed (`git.md:383` `#### 7.6 Reftable [2.45] [2.46] [Git 3.0] [Internals]`).

| File | Tag | Uses | Meaning (from the file's legend) |
|---|---|---:|---|
| DSA | `[Synthesis]` | 10 | click session; few new facts, many derivations (`:53`) |
| DSA | `[Advanced]` | 14 | graduate-level; nothing in the core depends on it (`:54`) |
| DSA | `[Overview]` | 8 | what a structure achieves and its key idea, not a full construction (`:55`) |
| GD | `[Synthesis]` | 19 | click session (`:59`) |
| GD | `[Exercise]` | 11 | goal reached by doing a small design task in the session (`:60`) |
| GD | `[Math]` | 4 chapter headings, 0 sessions | needs arithmetic or probability worked by hand (`:61`) |
| GD | `[Contested]` | 5 | goal is a debate; hold the positions and why (`:62`) |
| GD | `[Regulation]` | 1 chapter heading + 1 Notes heading, 0 sessions | claims about laws or regulator decisions that can change (`:63`) |
| git | `[2.26]` … `[2.56]` | 21 distinct versions, 83 uses | behaviour added or changed in that feature release (`:57`) |
| git | `[2.98-dev]` | 8 | merged to `master` for 2.98, not released (`:58`) |
| git | `[Git 3.0]` | 8 | planned breaking change in `BreakingChanges.adoc` (`:59`) |
| git | `[Experimental]` | 2 | manual page marks the command EXPERIMENTAL (`:60`); the legend names `git format-rev` but its session (13.1, `:583`) carries only `[2.55] [2.56]` and says "(experimental)" in Scope |
| git | `[Internals]` | 9 | goal is about implementation (`:61`) |
| git | `[contrib]` | 1 | centred on `contrib/` (`:62`) |
| git | `[Third-party]` | 2 | centred on a tool outside git.git (`:63`) |
| git | `[Synthesis]` | 16 | click session (`:64`) |
| PG | `[PG15]` … `[PG18]` | 8 / 8 / 12 / 41 (one is Chapter 40) | behaviour added or changed in that major release (`:53`) |
| PG | `[PG19]` | 30 | PostgreSQL 19, RC2 on the snapshot date; provisional (`:54`) |
| PG | `[Internals]` | 7 | goal is about implementation (`:55`) |
| PG | `[contrib]` | 4 | centred on an additional supplied module (`:56`) |
| PG | `[Synthesis]` | 14 | click session (`:57`) |
| JS | `[ES20xx]` | ES2020 3, ES2021 1, ES2022 4, ES2023 1, ES2024 2, ES2025 3, ES2026 3, plus composites | feature added in that edition (`:39`) |
| JS | `[ES2027 draft]` | 2 (+ composites) | Stage 4, merged into the editor's draft (`:40`) |
| JS | `[Stage 4 – not yet merged]` | 2 | finished; spec text in a pending PR (Temporal) (`:41`) |
| JS | `[Stage 3]` / `[Stage 2.7]` / `[Stage 2]` | used as `[Stage 3 / 2.7 / 2]` 2, `[Stage 2.7]` 1 | active proposals, taught as previews (`:42`) |
| JS | `[ECMA-402]` | 3 | the Intl standard (`:43`) |
| JS | `[Host: HTML]` / `[Host: Node]` / `[Host: DOM]` | `[Host: DOM]` 1 session (27.5); `[Host: HTML / DOM]` and `[Host: Node]` on appendix headings | defined by a host, not ECMAScript (`:44`) |
| JS | `[Non-normative]` | 1 appendix heading; also `[mostly Non-normative]` (31.1), `[Non-normative / security]` (11.8) | engine behaviour or practice no spec requires (`:45`) |

Tag forms in JS headings that its legend does not declare: `[advanced]` (32.4, `javascript.md:1497`), `[incl. …]` 11 times (e.g. `[incl. ES2026 upsert]` 21.1, `:1049`), slash composites `[ES2020/ES2021]` (5.5, `:317`) and `[ES2026 / ES2027 draft]` (17.2, `:925`), `[mostly Non-normative]`, `[Non-normative / security]`. The legend's first sentence also contradicts itself: "Each session title carries a tag. A session about a stable feature that is standard in ES2026 has no tag." (`javascript.md:37`); 44 of 182 session headings carry a tag.

CLM, math, SD and ITF have no heading tags. They mark kinds in prose:

- `(click session)` in the title: JS 5.9, 6.6, 26.6, 37.3 (`javascript.md:349, 405, 1237, 1631`); ITF RE 8 (`interview-fast-track.md:213`).
- `(synthesis)` in a pointer title: ITF DSA 64.13, 64.14 (`interview-fast-track.md:87-88`).
- `**Goal:** Synthesis:` prefix: SD, 10 sessions (e.g. `system-design.md:608`, `703`).
- `(optional)`: math, 1 chapter and 2 sessions (`math.md:1180, 1360, 1490`), defined at `math.md:36`.

### Inline version notes

git and PG also annotate individual clauses inside Scope/Key concepts with a parenthesised version: git `(2.NN)` 76 lines (e.g. `` `%(decorate)` 2.43 ``; legend reference "inline "(2.NN)"" at `git.md:1944`); PG `(PG15)`…`(PG19)` 85 lines. These are the "tagged clauses" that the ordering rationale lets a learner on an older version skip (`git.md:37`, `postgresql.md:33`). Neither legend defines the inline form.

### Bracketed source keys (not status tags)

- CLM: `[BASH]`, `[POSIX]`, `[POSIX-RE]`, `[ZSH]`, `[CU]`, `[SED]`, `[GAWK]`, `[GREP]`, `[FIND]`, `[RL]`, `[AW: Page]`, plus `name(N)` for man pages (`command-line-mastery.md:30-45`).
- math: `[CCSS-N]`, `[OS-Calc1]`, `[MIT-18.06]` etc., defined in back-matter Sources (`math.md:1534-1567`) and introduced as "Source tags" (`math.md:35`).

## Numbering and depth

| File | Heading depth used | Grouping levels above a session | Numbering |
|---|---|---|---|
| CLM | H1 title; H2 front sections, Parts, appendices, Sources; H3 front subsections and sessions | 1 (Part) | Parts Roman; sessions `### N.` global 1–134 (`command-line-mastery.md:53`) |
| DSA, GD, git, PG | H1 title, `# Table of contents`, `# Notes and open questions`; H2 front sections, Parts, Notes subsections; H3 front subsections, chapters; H4 sessions | 2 (Part, Chapter) | Parts Roman; `Chapter N` global across the map; session `C.S`, so the Part number is not in the ID ("session `22.6` is the sixth session of Chapter 22", `data-structures-and-algorithms.md:3`) |
| JS | as above, plus H1 `# Optional appendices`, H2 `## Appendix A — …` | 2 in the core; 1 in appendices (no chapter) | as above; appendix sessions `A.1`…`C.3` |
| math | H1 title; H2 Preamble, Parts, Sources; H3 front subsections and chapters; sessions are bullets | 2 (Part, Chapter) | Parts Arabic; `P.C.S` ("`7.5.2` is Part 7 … Chapter 5 … Session 2", `math.md:33`) |
| SD | H1 title; H2 front sections, Parts, Sources; H3 chapters; sessions are bullets | 2 (Part, Chapter) | Parts Arabic; `P.C.S` ("Each numbered leaf (e.g. `9.1.3`)", `system-design.md:9`) |
| ITF | H1 title, Schedule, Optional extensions, New sessions; H2 weeks and tracks; H4 sessions (H3 skipped) | 1 (week or track) | own sessions `PREFIX n` (`TS`, `RE`, `NX`, `WEB`); pointers `PREFIX id` using each map's own ID (`DSA 64.3`, `SD 22.7.4`, `PG 4.2`) |

Two ID schemes collide when files are referenced from each other: `12.1.4` is a `P.C.S` ID in math but `12.1` would be `Chapter.Session` in the chaptered maps; ITF resolves this with a prefix, GD with a backticked filename (`` `math.md` 12.1.4 ``).

## Field legends, word for word

Each block is copied verbatim from the cited lines.

### `command-line-mastery.md:9-19` (legend given as methodology bullets; no table)

```markdown
## How this map fits learnharness

The terms below come from `learnharness/docs/teaching-methodology.md`.

- **One session, one goal understanding.** Each session has a **Goal**: a single proposition that should *feel obviously true* to the learner by the end (§2). It is a statement, not a list of commands. The listed commands are what the goal lets the learner *derive*, not what they memorise.
- **Generators.** These are the few base facts that let a pile of loose facts in that topic "collapse into a structure" (§3). For example, "the shell expands, then executes; the program never sees your glob" generates most quoting and globbing behaviour. Planning should build the session's minimal tree around these.
- **Foundations.** Some facts are arbitrary conventions that can't be derived from anything (fd numbers, signal numbers, filesystem paths, unit-file section names). They are marked **Foundation** where they matter. They should be placed as-is: stated plainly and, where possible, motivated by a real problem (§6).
- **Scope = a coarse plan view, not lesson segments.** The **Scope** line is the landscape the session covers (§7b). It is a boundary for the planner, not a sequence of chapters to teach in order (§10.4). Anything not on the path to the Goal belongs to another session (§7b: "coverage is not the goal"). The map as a whole is exhaustive; each session is deliberately minimal.
- **Prereqs = the assumed current understanding.** Prereqs list only *direct* dependencies, and their prerequisites are implied. The prober (§10.1) should confirm these are held and prune anything already held. When a prereq is shaky, the right move is a short repair of that prereq, not teaching on top of it (§5).
- **Sources are logistics the system owns.** Every session cites primary sources so that the tutor, not the learner, does the fact-checking (§7a, §10.6).
- **Shells.** POSIX vs bash vs zsh differences are noted wherever behaviour diverges. Parts II–III teach the shell language on **bash with POSIX as the baseline**, because scripts, PKGBUILDs and `/usr/bin/sh` on Arch are all bash. Zsh is the interactive shell here, so zsh deltas are flagged inline and Part XIII covers zsh in depth.
```

### `data-structures-and-algorithms.md:35-47`

```markdown
## Per-session fields

| Field | Meaning |
|---|---|
| **Goal** | The goal understanding: what should *feel obviously true* at the end. |
| **Scope** | The boundary of the session (coarse plan view). |
| **Key concepts** | Raw material for planning the minimal tree. |
| **Foundations** | (Only where present.) Facts that must be accepted as-is, stated unconditionally. |
| **Prereqs** | Direct prerequisite sessions, all earlier in the map. A dash means none. |
| **Check** | One exit/skip-probe question. |
| **Sources** | The textbooks, course lectures and original papers that own the session's claims. |

Each chapter also opens with a **Click** line: the few generators its sessions' facts collapse into.
```

### `game-design.md:41-53`

```markdown
## Per-session fields

| Field | Meaning |
|---|---|
| **Goal** | The goal understanding: what should *feel obviously true* at the end. |
| **Scope** | The boundary of the session (coarse plan view). |
| **Key concepts** | Raw material for planning the minimal tree. |
| **Foundations** | (Only where present.) Facts that must be accepted as-is, stated unconditionally. |
| **Prereqs** | Direct prerequisite sessions, all earlier in the map. A dash means none. |
| **Check** | One exit/skip-probe question, usually a small design or diagnosis problem. |
| **Sources** | The primary sources that own the session's claims. |

Each chapter also opens with a **Click** line: the few generators its sessions' facts collapse into.
```

### `git.md:39-51`

```markdown
## Per-session fields

| Field | Meaning |
|---|---|
| **Goal** | The goal understanding: what should *feel obviously true* at the end. |
| **Scope** | The boundary of the session (coarse plan view). |
| **Key concepts** | Raw material for planning the minimal tree. |
| **Foundations** | (Only where present.) Facts that must be accepted as-is, stated unconditionally. |
| **Prereqs** | Direct prerequisite sessions, all earlier in the map. A dash means none. |
| **Check** | One exit/skip-probe question. |
| **Sources** | The primary sources that own the session's claims. |

Each chapter also opens with a **Click** line: the few generators its sessions' facts collapse into.
```

### `postgresql.md:35-47`

```markdown
## Per-session fields

| Field | Meaning |
|---|---|
| **Goal** | The goal understanding: what should *feel obviously true* at the end. |
| **Scope** | The boundary of the session (coarse plan view). |
| **Key concepts** | Raw material for planning the minimal tree. |
| **Foundations** | (Only where present.) Facts that must be accepted as-is, stated unconditionally. |
| **Prereqs** | Direct prerequisite sessions, all earlier in the map. A dash means none. |
| **Check** | One exit/skip-probe question. |
| **Sources** | The primary sources that own the session's claims. |

Each chapter also opens with a **Click** line: the few generators its sessions' facts collapse into.
```

### `javascript.md:23-33`

```markdown
## Per-session fields

| Field | Meaning |
|---|---|
| **Goal** | The goal understanding: what should *feel obviously true* at the end. |
| **Scope** | The 1–2 line boundary of the session. |
| **Key concepts** | Raw material for planning the minimal tree. |
| **Foundations** | (Only where present.) Facts that must be accepted as-is, stated unconditionally. |
| **Prereqs** | Direct prerequisite sessions. A dash means the session has none. |
| **Check** | One exit/skip-probe question. |
| **Sources** | The primary source that owns each claim: ECMA-262 or ECMA-402 section, WHATWG HTML, Node.js docs, MDN, or the TC39 proposal repository. |
```

### `math.md:31-36`

```markdown
### How to read the numbering

- **`P.C.S`** = Part · Chapter · Session. For example, `7.5.2` is Part 7 (Single-Variable Calculus), Chapter 5 (Analytical applications), Session 2 (Rolle's theorem and the Mean Value Theorem).
- Each session builds on **the session just before it** unless the chapter has clearly moved to a new topic. **`Needs:`** lists every *other* direct prerequisite, by number and title. Only direct prerequisites are listed; the ones further back are implied.
- **Source tags** such as `[OS-Calc1] §4.4` or `[MIT-18.06] L21` point to the Sources section at the end. A Part's tag covers its scope; a chapter's tag covers that chapter's content and order. Lecture numbers `Lnn` refer to the fetched lecture lists of the MIT courses.
- "(optional)" marks sessions or chapters beyond the core that are not needed later, except where another session's `Needs:` names them.
```

### `system-design.md:9-11` and `35-36`

```markdown
**What a session is.** Each numbered leaf (e.g. `9.1.3`) is sized for one LearnHarness Teach session. The *Goal* line is phrased as the understanding that should end up feeling obviously true — usually a "why", not a list of facts — so the prober has a concrete target and the planner can find the minimal path to it. Where a leaf would need more than one "click", it has been split. Several leaves are explicitly "synthesis" sessions that connect earlier nodes rather than add new ones; these make good Practice sessions too.

**Ordering.** Parts go from foundations to applications. Within a chapter, each session assumes the one before it. Any *additional* dependency is listed as `Prereq:` with session numbers; if no `Prereq:` is given, the only dependency is the previous session (or, for the first session of a chapter, the chapter's stated prerequisites). The order is a valid topological order of the dependency graph: no session lists a prerequisite that comes after it. Part 22 (case studies) can be taken in any order once its listed prerequisites are met.
```

```markdown
**Format of a session line.**
`N.N.N Title` — **Goal:** the understanding to reach. · **Prereq:** extra dependencies. · **Src:** citations.
```

### `interview-fast-track.md:111`

```markdown
These follow the same per-session fields as the other maps: **Goal** (what should feel obviously true at the end), **Scope**, **Key concepts**, **Prereqs**, **Check** (exit/skip probe) and **Sources**. Framework sessions are version-sensitive. They target **TypeScript 5.x, React 19 and the Next.js App Router (v15/16)**. Confirm the version a target company uses before deep-diving Next.js caching, which changed between major versions.
```

### Differences among the five legend tables

Taking DSA as the base, the other four tables differ only in these rows:

| Row | DSA | GD | git | PG | JS |
|---|---|---|---|---|---|
| Scope | The boundary of the session (coarse plan view). | same | same | same | The 1–2 line boundary of the session. |
| Prereqs | Direct prerequisite sessions, all earlier in the map. A dash means none. | same | same | same | Direct prerequisite sessions. A dash means the session has none. |
| Check | One exit/skip-probe question. | One exit/skip-probe question, usually a small design or diagnosis problem. | same as DSA | same as DSA | same as DSA |
| Sources | The textbooks, course lectures and original papers that own the session's claims. | The primary sources that own the session's claims. | same as GD | same as GD | The primary source that owns each claim: ECMA-262 or ECMA-402 section, WHATWG HTML, Node.js docs, MDN, or the TC39 proposal repository. |
| Click note after the table | present | present | present | present | absent |

## Tag legends, word for word

### `data-structures-and-algorithms.md:49-55`

```markdown
### Tags

A session with no tag is core material found in standard undergraduate texts (CLRS, Sedgewick & Wayne, Kleinberg & Tardos).

- **`[Synthesis]`**: a click session; few new facts, many derivations.
- **`[Advanced]`**: graduate-level material (typically 6.046J/6.851/CS166 depth). Nothing in the core depends on it unless a later session lists it as a prereq.
- **`[Overview]`**: the session's goal is what a structure or algorithm achieves and the idea that makes it work, not a full construction or proof (used where the full treatment is a research paper, e.g. Ukkonen's algorithm, fusion trees, Edmonds' blossoms).
```

### `game-design.md:55-63`

```markdown
### Tags

Game design has no versions, so the tags mark the *kind* of session rather than its currency.

- **`[Synthesis]`**: a click session; few new facts, many derivations.
- **`[Exercise]`**: the session's goal is reached by doing a small design task (paper prototype, spreadsheet, diagram, playtest) in the session; it still has one goal proposition.
- **`[Math]`**: the session needs arithmetic or probability worked by hand; a learner weak on fractions or expected value should take the cited sessions in `math.md` first.
- **`[Contested]`**: the session's goal is a debate, not a settled fact; the goal is to hold *the positions and why each is held*, and Sources cite each side.
- **`[Regulation]`**: claims are about laws or regulator decisions that can change; dates are given and the snapshot date applies.
```

### `git.md:53-64`

```markdown
### Tags

A session about long-standing behaviour has no version tag.

- **`[2.26]` … `[2.56]`**: the session teaches behaviour added or changed in that feature release (the release notes cited in Sources say what). Tags are given systematically for releases from 2.38 on, and for a few older milestones that still shape behaviour (protocol v2 default in 2.26/2.29, `--force-if-includes` in 2.30, SSH signing in 2.34, cruft packs and cone-mode-only sparse checkout in 2.37). 2.56 is the target version, so `[2.56]` items are current.
- **`[2.98-dev]`**: merged to `master` for the next feature release (2.98), listed in `Documentation/RelNotes/2.98.0.adoc` on the snapshot date but not yet released. Cited against `master`; treat as provisional.
- **`[Git 3.0]`**: a planned breaking change recorded in `Documentation/BreakingChanges.adoc` (no release date is set).
- **`[Experimental]`**: the command's own manual page marks it EXPERIMENTAL (`git replay`, `git history`, `git format-rev`).
- **`[Internals]`**: the session's goal is about implementation, owned by technical documents and source files as much as by the manual.
- **`[contrib]`**: centred on something shipped in `contrib/` rather than core (`git subtree`).
- **`[Third-party]`**: centred on a tool outside git.git (`git filter-repo`, Git LFS), cited to that tool's own documentation.
- **`[Synthesis]`**: a click session; few new facts, many derivations.
```

### `postgresql.md:49-57`

```markdown
### Tags

A session about long-standing behaviour has no version tag.

- **`[PG15]` … `[PG18]`**: the session teaches behaviour added or changed in that major release (the release notes cited in Sources say what). PG18 is the target version, so `[PG18]` items are current.
- **`[PG19]`**: behaviour from PostgreSQL 19, at Release Candidate 2 on the snapshot date (GA planned 2026-11-19). Cited against `/docs/19/` and the PG19 release notes; treat as provisional until GA.
- **`[Internals]`**: the session's goal is about implementation, owned by the source tree as much as by the manual.
- **`[contrib]`**: centred on an additional supplied module (`CREATE EXTENSION` required).
- **`[Synthesis]`**: a click session; few new facts, many derivations.
```

### `javascript.md:35-45`

```markdown
### Status tags

Each session title carries a tag. A session about a stable feature that is standard in ES2026 has no tag.

- **`[ES20xx]`**: the session centres on a feature added in that edition (shown for ES2020 and later). These features are standard.
- **`[ES2027 draft]`**: Stage 4, merged into the ECMA-262 editor's draft but not yet in a published edition.
- **`[Stage 4 – not yet merged]`**: finished, but the spec text is still in a pending PR (Temporal).
- **`[Stage 3]` / `[Stage 2.7]` / `[Stage 2]`**: active proposals, not part of the language. Taught as previews.
- **`[ECMA-402]`**: the Intl API standard, a separate Ecma standard alongside ECMA-262.
- **`[Host: HTML]` / `[Host: Node]` / `[Host: DOM]`**: defined by a host environment, not by ECMAScript.
- **`[Non-normative]`**: engine behaviour or practice that no specification requires.
```

### `command-line-mastery.md:30-45` (source abbreviations, the only bracket legend in CLM)

```markdown
### Source abbreviations

| Tag | Source |
|---|---|
| **[BASH]** | GNU Bash Reference Manual (5.3), section numbers as in `info bash` — https://www.gnu.org/software/bash/manual/ |
| **[POSIX]** | POSIX.1-2024 XCU ch. 2 "Shell Command Language" — https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html ; utility pages at `.../utilities/<name>.html` |
| **[POSIX-RE]** | POSIX.1-2024 XBD ch. 9 "Regular Expressions" — https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap09.html |
| **[ZSH]** | Zsh Manual (5.9), chapter numbers as in https://zsh.sourceforge.io/Doc/Release/zsh_toc.html ; also `man zshall` |
| **[CU]** | GNU Coreutils manual, chapter numbers as in `info coreutils` — https://www.gnu.org/software/coreutils/manual/ |
| **[SED]** | GNU sed manual — https://www.gnu.org/software/sed/manual/sed.html |
| **[GAWK]** | GAWK: Effective AWK Programming — https://www.gnu.org/software/gawk/manual/gawk.html |
| **[GREP]** | GNU grep manual — https://www.gnu.org/software/grep/manual/grep.html |
| **[FIND]** | GNU Findutils manual — https://www.gnu.org/software/findutils/manual/html_mono/find.html |
| **[RL]** | GNU Readline (in [BASH] ch. 8) — https://tiswww.case.edu/php/chet/readline/rltop.html |
| **name(N)** | man page; Linux/systemd pages at https://man7.org/linux/man-pages/ and https://www.freedesktop.org/software/systemd/man/latest/ ; Arch/pacman pages at https://man.archlinux.org/ |
| **[AW: Page]** | Arch Wiki — https://wiki.archlinux.org/title/Page |
```
