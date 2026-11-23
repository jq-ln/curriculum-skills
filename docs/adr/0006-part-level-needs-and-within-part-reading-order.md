# 0006: Part-level derived Needs, and a reading order that holds only inside a Part

Status: Accepted

Evidence: [Making the branch graph visible in the doc set](https://github.com/jq-ln/curriculum-skills/issues/41), specified in [Curricula with a core Part and Part-level Needs](https://github.com/jq-ln/curriculum-skills/issues/54).

## Context

A Curriculum now starts with a core Part of what day-to-day practice needs, and every later Part is ordered by what it needs, so several Parts can open straight after the core. Format version 1 showed none of that. The nav line's Prev and Next ran straight across Part boundaries, implying one linear read, and nothing at Part level said which Parts depend on which. Subsection Prereqs already record every dependency, but a learner choosing their next Part would have to open every Subsection to find them.

## Decision

- Each Part has a derived Needs Field, after Intro, listing the other Parts of the same Curriculum that its Subsections' Prereqs land in, each once, in ID order. It's present only when there's at least one.
- The index's Parts table ends with a Needs column holding the same Parts as linked IDs, so the whole branch structure shows on one page.
- Needs is direct and unreduced, mirroring Subsection Prereqs: the core appears wherever a unit needs it directly.
- A Prereq in another Curriculum adds no entry, because whether its copy is found depends on the machine, and Needs must derive the same everywhere.
- Prev and Next follow ID order only within a Part. A Part's first Subsection has no Prev and its last has no Next. The Index and Part links stay, so a learner moves on to another Part from there.

Alternatives weighed in #41 and rejected:

- **Tiers**, a derived depth number per Part: the Needs column already shows which Parts need only the core, and Ordering rationale can describe any grouping in prose.
- **Reverse links**, a "Needed by" Field: on the core it would list nearly every Part, and it adds a second derived view of the same edges.
- **Section-level Needs**: Subsection Prereqs already carry the fine grain, such as only 2 of a Part's 7 units needing another Part, and a Section-level copy would add Fields without a decision it helps a learner make.
- **Transitive reduction** of Needs: it would hide a direct dependency behind an intermediate Part and make Needs differ in kind from Prereqs. A later skill that wants a transitive or reduced view computes it from the direct one.

## Consequences

- Needs is derived content, so `check` fails on a hand edit to it or to a Needs cell through the existing re-derive comparison, with no new rule.
- The format changed what `check` accepts, so it moved to Format version 2 ([ADR 0004](0004-integer-format-version.md)), and every Format version 1 doc set fails `check` until it's rebuilt.
- The nav line no longer reads as one path through the Curriculum. A learner finishing a Part picks the next from the index's Parts table or a Part's Needs.
- The core needs no marker: it's the first Part, and because a Prereq must come earlier in global ID order, it's closed under Prereqs by construction.
