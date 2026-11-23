"""Tests for skills/build-curriculum/scripts/build.py, driven only through its CLI."""

import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "build-curriculum" / "scripts" / "build.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
GIT = FIXTURES / "git"
DRAFT = GIT / "draft"
GOLDEN = GIT / "golden"
INVALID = FIXTURES / "check"
SUBSECTION_TITLE = "Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot"
SUBSECTION_SLUG = "content-addressed-objects-blobs-trees-commits-and-the-naive"
SUBSECTION_FILE = f"GIT-01.01.01-{SUBSECTION_SLUG}.md"  # the first Subsection
PART_FILE = "GIT-01-repository-internals.md"
REFS_FILE = "GIT-01.01.02-refs.md"
# A paragraph after the nav line, a line right after it, and a line right before it
NAV_LINE_EXTRA = ["nav-line-extra-content", "nav-line-extra-line", "nav-line-after-note"]
ANCESTRY_FILE = "GIT-02.01.01-ancestry.md"
PART_2_FILE = "GIT-02-history.md"
INDEX_SECTION_FILE = "GIT-01.02-the-index.md"
INDEX_SUBSECTION_FILE = "GIT-01.02.01-the-index-as-a-staging-snapshot.md"
SECTION_FILE = "GIT-01.01-objects.md"
CAT_FILE = "GIT-03.01.01-cat-file.md"  # in the Optional Part, using a tag inline
APPENDIX_FILE = "GIT-appendix-manual-coverage.md"  # applies to GIT-01 and GIT-02.01
COMMIT_GRAPH_FILE = "GIT-02.01-the-commit-graph.md"
PLUMBING_FILE = "GIT-03-plumbing.md"  # the Optional Part


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def tree(root):
    """Every file under root, as relative paths, hidden files included."""
    return sorted(
        str(Path(dirpath, name).relative_to(root))
        for dirpath, _, names in os.walk(root)
        for name in names
    )


def replace(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"{old!r} isn't in {path.name} exactly once"
    path.write_text(text.replace(old, new), encoding="utf-8")


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def assertPasses(self, doc_set):
        result = run("check", doc_set)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def assertErrors(self, doc_set, *lines):
        """check exits 1 and prints exactly these error lines, in any order."""
        result = run("check", doc_set)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertCountEqual(result.stdout.splitlines(), lines)

    def copy(self, src):
        dst = self.tmp / src.name
        shutil.copytree(src, dst)
        return dst


class Split(TempDirTestCase):
    def test_then_derive_reproduces_the_golden_doc_set_byte_for_byte(self):
        out = self.tmp / "git"
        split = run("split", DRAFT, out)
        self.assertEqual(split.returncode, 0, split.stderr)
        derive = run("derive", out)
        self.assertEqual(derive.returncode, 0, derive.stderr)

        self.assertEqual(tree(out), tree(GOLDEN))
        for name in tree(GOLDEN):
            with self.subTest(file=name):
                self.assertTrue(
                    filecmp.cmp(out / name, GOLDEN / name, shallow=False),
                    f"{name} differs from the golden copy",
                )

    def assertStops(self, draft, line):
        """split exits 1 with this error and writes nothing."""
        out = self.tmp / "git"
        result = run("split", draft, out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(line, result.stderr.splitlines())
        self.assertFalse(out.exists())

    def test_stops_on_content_before_a_docs_first_field(self):
        draft = self.copy(DRAFT)
        h1 = f"# GIT-01.01.01 {SUBSECTION_TITLE}\n"
        replace(draft / "part-01.md", h1, h1 + "\nLead prose here.\n")
        self.assertStops(draft, f"split: part-01.md: # GIT-01.01.01 {SUBSECTION_TITLE}: has content before its first Field")

    def test_stops_on_content_before_a_merge_blocks_first_field(self):
        draft = self.copy(DRAFT)
        with open(draft / "part-03.md", "a") as f:
            f.write("\nGIT-03.01.01: the manual and --help disagree on -p for trees.\n")
        self.assertStops(draft, "split: part-03.md: # GIT Part notes: has content before its first Field")

    def test_stops_on_a_title_with_an_empty_slug(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "# GIT-01 Repository internals", "# GIT-01 ———")
        self.assertStops(draft, "split: outline.md: # GIT-01 ———: title has an empty slug")

    def test_stops_on_an_id_with_a_00_level(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "# GIT-01 Repository internals", "# GIT-00 Repository internals")
        self.assertStops(
            draft,
            "split: outline.md: # GIT-00 Repository internals: GIT-00 isn't an ID: each level is two digits from 01 to 99",
        )

    def test_names_the_file_with_text_before_its_first_h1(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-01.md", "# GIT-01.01.01", "Stray text.\n\n# GIT-01.01.01")
        self.assertStops(draft, "split: part-01.md: doesn't start with an H1")

    def test_names_the_file_with_a_setext_heading(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "None so far.\n", "None so far.\n---\n")
        self.assertStops(draft, "split: outline.md: has a setext heading, `None so far.` over `---`; use an ATX heading")

    def test_reads_a_draft_file_that_starts_with_a_blank_line(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "# Git (GIT)\n", "\n# Git (GIT)\n")
        out = self.tmp / "git"
        result = run("split", draft, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run("derive", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(filecmp.cmp(out / "index.md", GOLDEN / "index.md", shallow=False))

    def test_writes_an_empty_field_with_one_blank_line_after_it(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "## Target version\n\n2.47.1\n", "## Target version\n")
        out = self.tmp / "git"
        result = run("split", draft, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Target version\n\n## Format version\n", (out / "index.md").read_text(encoding="utf-8"))

    def test_stops_on_a_curriculum_name_with_a_character_that_breaks_links(self):
        draft = self.copy(DRAFT)
        replace(draft / "outline.md", "# Git (GIT)", "# Git [core] (GIT)")
        self.assertStops(
            draft, "split: outline.md: # Git [core] (GIT): name contains [ ], which would break a link or table copying it"
        )

    def test_ignores_a_unit_inside_an_html_comment(self):
        draft = self.copy(DRAFT)
        with (draft / "part-01.md").open("a", encoding="utf-8") as f:
            f.write("\n<!--\n# GIT-02 Later\n\n## Intro\n-->\n")
        out = self.tmp / "git"
        result = run("split", draft, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree(out), tree(GOLDEN))

    def test_stops_on_a_draft_file_that_isnt_utf_8(self):
        draft = self.copy(DRAFT)
        (draft / "part-01.md").write_bytes(b"# GIT-01.01.01 \xff\n")
        self.assertStops(draft, "split: part-01.md: isn't valid UTF-8")

    def test_stops_on_a_batch_whose_sections_come_before_an_earlier_batchs(self):
        draft = self.copy(DRAFT)
        a, b = (draft / "part-01.md").read_text(encoding="utf-8"), (draft / "part-01-b.md").read_text(encoding="utf-8")
        (draft / "part-01.md").write_text(b, encoding="utf-8")
        (draft / "part-01-b.md").write_text(a, encoding="utf-8")
        self.assertStops(
            draft,
            f"split: part-01-b.md: # GIT-01.01.01 {SUBSECTION_TITLE}: comes after GIT-01.02.01; "
            "a Part's files hold its Sections in ID order",
        )

    def test_stops_on_a_section_split_across_batches(self):
        draft = self.copy(DRAFT)
        text = (draft / "part-01.md").read_text(encoding="utf-8")
        at = text.index("# GIT-01.01.02")
        (draft / "part-01.md").write_text(text[:at], encoding="utf-8")
        batch = (draft / "part-01-b.md").read_text(encoding="utf-8")
        (draft / "part-01-b.md").write_text(text[at:] + "\n" + batch, encoding="utf-8")
        self.assertStops(
            draft, "split: part-01-b.md: # GIT-01.01.02 Refs: Section GIT-01.01 is also in part-01.md; a batch holds whole Sections"
        )

    def test_stops_on_a_part_file_holding_another_parts_unit(self):
        draft = self.copy(DRAFT)
        (draft / "part-02.md").rename(draft / "part-03-b.md")
        self.assertStops(draft, "split: part-03-b.md: # GIT-02.01.01 Ancestry: isn't in GIT-03, the Part this file fills")

    def test_stops_on_a_part_file_adding_a_subsection_the_outline_lacks(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-02.md", "# GIT Sources added", "# GIT-02.01.02 Merge bases\n\n## Scope\n\nLater.\n\n# GIT Sources added")
        self.assertStops(
            draft, "split: part-02.md: # GIT-02.01.02 Merge bases: isn't a Subsection of outline.md; a part file fills the Outline's Subsections"
        )

    def test_stops_on_a_part_file_holding_a_field_the_outline_fixes(self):
        for field, content in [("Tags", "- Synthesis"), ("Goal", "Refs move."), ("Prereqs", "None")]:
            with self.subTest(field=field):
                draft = self.copy(DRAFT)
                # GIT-01.01.02 has no Tags in outline.md, so only the part-file rule can stop this
                replace(draft / "part-01.md", "# GIT-01.01.02 Refs\n", f"# GIT-01.01.02 Refs\n\n## {field}\n\n{content}\n")
                self.assertStops(
                    draft,
                    f"split: part-01.md: # GIT-01.01.02 Refs: {field} is fixed by outline.md; "
                    "a part file holds Generators, Foundations, Scope, Key concepts, Check and Sources",
                )
                shutil.rmtree(draft)

    def test_stops_on_a_part_file_holding_a_section_doc(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-02.md", "# GIT-02.01.01 Ancestry\n", "# GIT-02.01 The commit graph\n\n## Generators\n\n- More.\n\n# GIT-02.01.01 Ancestry\n")
        self.assertStops(
            draft, "split: part-02.md: # GIT-02.01 The commit graph: isn't a Subsection of outline.md; a part file fills the Outline's Subsections"
        )

    def test_stops_on_a_draft_file_with_a_name_it_doesnt_read(self):
        draft = self.copy(DRAFT)
        (draft / "part-01-b.md").rename(draft / "part-1b.md")
        self.assertStops(draft, "split: part-1b.md: isn't outline.md, part-NN.md, part-NN-<letter>.md or appendix-<description>.md")

    def test_replaces_a_notes_field_holding_only_none_so_far(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-03.md", "# GIT Part notes\n", "# GIT Part notes\n\n## Judgement calls\n\n- The manual and `--help` disagree.\n")
        out = self.tmp / "git"
        result = run("split", draft, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "## Judgement calls\n\n- The manual and `--help` disagree.\n\n## Scope decisions\n",
            (out / "GIT-notes.md").read_text(encoding="utf-8"),
        )

    def test_keeps_an_abbreviation_added_with_another_expansion_for_check_to_report(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-01-b.md", "| man | Git manual pages, version 2.47.1 |", "| man | Git manual pages, version 2.46 |")
        out = self.tmp / "git"
        self.assertEqual(run("split", draft, out).returncode, 0)
        self.assertErrors(
            out,
            "GIT-sources.md: abbreviation man is defined more than once, as "
            "`Git manual pages, version 2.47.1` and `Git manual pages, version 2.46`",
        )

    def test_stops_on_a_merge_block_field_its_doc_lacks(self):
        draft = self.copy(DRAFT)
        replace(draft / "part-03.md", "# GIT Part notes\n", "# GIT Part notes\n\n## Summary\n\nDone.\n")
        self.assertStops(draft, "split: part-03.md: # GIT Part notes: Summary isn't a Field of the Notes doc")

    def test_stops_on_a_unit_after_a_merge_block(self):
        draft = self.copy(DRAFT)
        with (draft / "part-02.md").open("a", encoding="utf-8") as f:
            f.write("\n# GIT-02.01.02 Merge bases\n\n## Scope\n\nLater.\n")
        self.assertStops(
            draft, "split: part-02.md: # GIT-02.01.02 Merge bases: comes after a merge block, which goes at the end of a part file"
        )

    def test_stops_on_a_merge_block_in_the_outline(self):
        draft = self.copy(DRAFT)
        with (draft / "outline.md").open("a", encoding="utf-8") as f:
            f.write("\n# GIT Part notes\n")
        self.assertStops(draft, "split: outline.md: # GIT Part notes: a merge block goes at the end of a part file")

    def test_stops_on_an_appendix_outside_its_own_draft_file(self):
        draft = self.copy(DRAFT)
        with (draft / "outline.md").open("a", encoding="utf-8") as f:
            f.write("\n# GIT Appendix: Glossary\n\n## Purpose\n\nTerms.\n")
        self.assertStops(draft, "split: outline.md: # GIT Appendix: Glossary: an Appendix goes alone in its own appendix-<description>.md")

    def test_stops_on_an_output_path_that_is_a_file(self):
        out = self.tmp / "git"
        out.write_text("", encoding="utf-8")
        result = run("split", DRAFT, out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stderr.splitlines(), [f"split: {out}: already exists and isn't a directory"])


class Check(TempDirTestCase):
    def test_passes_the_golden_doc_set(self):
        result = run("check", GOLDEN)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    # One fixture per rule #18 names.

    def test_reports_a_missing_format_version(self):
        self.assertErrors(
            INVALID / "format-version-missing",
            "index.md: Format version is missing; this script reads Format version 2. "
            "Restore it from the history of index.md, such as `git log -p index.md`",
        )

    def test_rejects_a_format_version_1_doc_set_naming_both_numbers(self):
        self.assertErrors(
            INVALID / "format-version-mismatch",
            "index.md: Format version is 1, but this script reads Format version 2",
        )

    def test_reports_a_missing_required_field(self):
        self.assertErrors(INVALID / "field-missing", f"{SUBSECTION_FILE}: required Field Goal is missing")

    def test_reports_an_h1_id_that_differs_from_the_filename(self):
        self.assertErrors(
            INVALID / "id-mismatch",
            f"{SUBSECTION_FILE}: H1 ID GIT-01.01.02 differs from the filename's ID GIT-01.01.01",
        )

    def test_reports_an_id_with_an_unpadded_level(self):
        self.assertErrors(
            INVALID / "id-malformed",
            f"GIT-01.01.1-{SUBSECTION_SLUG}.md: GIT-01.01.1 isn't an ID: each level is two digits from 01 to 99",
        )

    def test_reports_a_filename_whose_slug_differs_from_the_title(self):
        self.assertErrors(
            INVALID / "filename-slug",
            f"GIT-01.01.01-objects.md: filename should be {SUBSECTION_FILE}, from its title; run derive to rename it",
            f"GIT-notes.md: link target {SUBSECTION_FILE} names no file in the doc set; run derive to rewrite it",
        )

    def test_reports_a_hand_edit_to_derived_content(self):
        self.assertErrors(
            INVALID / "context-edited",
            f"{SUBSECTION_FILE}: Field Context has `2026-11-20` where derive writes `2026-11-19`; edit its source and run derive",
        )

    def test_reports_each_edited_span_of_derived_content(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "- Snapshot: 2026-11-19\n", "- Snapshot: 2026-11-19 (approx.)\n")
        replace(doc_set / REFS_FILE, ": A commit pins a whole project state,", ": A commit pins a project state,")
        replace(doc_set / "GIT-tags.md", "- Where: inline\n- Uses: 1\n", "- Where: inline\n- Uses: 7\n")
        self.assertErrors(
            doc_set,
            f"{REFS_FILE}: Field Context has `(approx.)`, which derive doesn't write; edit its source and run derive",
            f"{REFS_FILE}: Field Prereqs lacks `whole`, which derive writes; edit its source and run derive",
            "GIT-tags.md: tag 2.46 has `7` where derive writes `1`; edit its source and run derive",
        )

    def test_reports_a_whitespace_edit_to_derived_content(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "  - A commit names one tree", "- A commit names one tree")
        self.assertErrors(
            doc_set, f"{REFS_FILE}: Field Context differs in whitespace from what derive writes; edit its source and run derive"
        )

    # One fixture per rule #19 names.

    def test_reports_an_own_code_id_naming_no_unit(self):
        self.assertErrors(INVALID / "id-unknown", f"{REFS_FILE}: GIT-09.01 names no unit")

    def test_reports_an_unknown_id_in_braces(self):
        self.assertErrors(INVALID / "id-in-braces", f"{REFS_FILE}: GIT-09.09 names no unit")

    def test_reports_a_link_target_that_isnt_a_bare_sibling_filename(self):
        self.assertErrors(
            INVALID / "link-target-form",
            "GIT-overview.md: link target ./GIT-02-history.md isn't a bare sibling filename or a same-file anchor; "
            "run derive to rewrite it",
        )

    def test_reports_a_link_target_naming_a_missing_file(self):
        self.assertErrors(
            INVALID / "link-target-missing",
            "GIT-overview.md: link target GIT-02-commits.md names no file in the doc set; run derive to rewrite it",
        )

    def test_reports_a_prereq_that_points_forward(self):
        self.assertErrors(INVALID / "prereq-forward", f"{REFS_FILE}: Prereq GIT-02.01.01 doesn't come before GIT-01.01.02")

    # One fixture per other rule this script added with #19.

    def test_reports_an_own_code_token_that_isnt_an_id(self):
        self.assertErrors(
            INVALID / "id-token-malformed", f"{REFS_FILE}: GIT-7 isn't an ID: each level is two digits from 01 to 99"
        )

    def test_reports_a_link_between_docs_naming_no_unit(self):
        self.assertErrors(
            INVALID / "link-names-no-unit",
            "GIT-notes.md: link [the overview](GIT-overview.md) names no unit or tag; write the unit's bare ID or the tag's marker instead",
        )

    def test_reports_a_link_target_naming_a_missing_heading(self):
        self.assertErrors(
            INVALID / "link-anchor-missing",
            f"GIT-overview.md: link target GIT-02-history.md#merges names no heading in {PART_2_FILE}; run derive to rewrite it",
        )

    def test_reports_a_prereq_naming_a_section(self):
        self.assertErrors(INVALID / "prereq-not-subsection", f"{REFS_FILE}: Prereq GIT-01.01 names no Subsection")

    def test_reports_a_prereq_with_a_qualifier(self):
        self.assertErrors(
            INVALID / "prereq-not-alone", f"{ANCESTRY_FILE}: Prereqs entry `GIT-01.01.01 (preview)` isn't an ID alone"
        )

    def test_reports_a_prereq_in_another_curriculum_that_isnt_a_subsection_id(self):
        self.assertErrors(INVALID / "prereq-other-code-level", f"{ANCESTRY_FILE}: Prereq MATH-03.01 isn't a Subsection ID")

    def test_reports_prereqs_that_arent_bullets(self):
        self.assertErrors(
            INVALID / "prereqs-not-bullets",
            f"{ANCESTRY_FILE}: Field Prereqs holds content other than bullets, or None alone",
        )

    # One fixture per rule #20 names.

    def test_reports_two_tags_with_one_anchor(self):
        self.assertErrors(INVALID / "tag-anchor-collision", "GIT-tags.md: tag 243 has the anchor 243, as tag 2.43 does")

    def test_reports_a_tag_whose_github_and_marksman_anchors_can_differ(self):
        self.assertErrors(
            INVALID / "tag-anchor-unstable",
            "GIT-tags.md: tag 2.46 — rc has the anchor 246--rc, on which GitHub's and marksman's slugs can differ",
        )

    def test_reports_a_tags_entry_naming_no_tag(self):
        self.assertErrors(INVALID / "tag-unknown", f"{INDEX_SECTION_FILE}: Tags entry 2.44 names no tag in GIT-tags.md")

    def test_reports_a_prereq_inside_an_optional_unit_the_subsection_is_outside(self):
        self.assertErrors(
            INVALID / "optional-dependant",
            f"{ANCESTRY_FILE}: Prereq GIT-01.02.01 is inside Optional Section GIT-01.02, which no unit outside it may depend on",
        )

    def test_reports_a_tag_marker_whose_where_lacks_inline(self):
        self.assertErrors(
            INVALID / "tag-inline-not-allowed",
            f"{REFS_FILE}: tag Synthesis is used inline, but its Where in GIT-tags.md lacks inline",
        )

    def test_reports_a_tags_entry_whose_where_lacks_doc(self):
        self.assertErrors(
            INVALID / "tag-entry-not-doc",
            f"{SECTION_FILE}: Tags entry 2.46: its Where in GIT-tags.md lacks doc",
        )

    # The other tag rules, each on a copy of the golden doc set.

    def test_reports_a_tag_name_with_a_character_that_breaks_markers_or_links(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-tags.md", "## 2.46\n", "## 2.46 [rc]\n")
        self.assertErrors(doc_set, "GIT-tags.md: tag 2.46 [rc] contains [ ], which a tag name can't")

    def test_reports_a_meaning_ending_like_an_origin_mark(self):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / "GIT-tags.md", "a", encoding="utf-8") as f:
            f.write("\n## Shell\n\n- Meaning: Every example runs in a POSIX shell (inline)\n- Where: doc\n")
        self.assertErrors(
            doc_set,
            "GIT-tags.md: tag Shell has a Meaning ending in (from <ID>) or (inline), which marks a derived Tags entry",
        )

    def assertOriginMarkNameReported(self, name):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / "GIT-tags.md", "a", encoding="utf-8") as f:
            f.write(f"\n## {name}\n\n- Meaning: Not yet reviewed.\n- Where: doc\n")
        self.assertErrors(
            doc_set,
            f"GIT-tags.md: tag {name} has a name ending in (from <ID>) or (inline), which marks a derived Tags entry",
        )

    def test_reports_a_tag_name_ending_in_inline(self):
        self.assertOriginMarkNameReported("Draft (inline)")

    def test_reports_a_tag_name_ending_in_from_id(self):
        self.assertOriginMarkNameReported("Draft (from GIT-03)")

    def test_reports_a_tag_whose_anchor_is_a_standard_tags(self):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / "GIT-tags.md", "a", encoding="utf-8") as f:
            f.write("\n## optional\n\n- Meaning: Lower case.\n- Where: inline\n")
        self.assertErrors(doc_set, "GIT-tags.md: tag optional has the anchor optional, as tag Optional does")

    def test_reports_a_tag_with_content_other_than_its_bullets(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-tags.md", "- Where: inline\n", "- Where: inline\n\nA family of release tags.\n")
        self.assertErrors(doc_set, "GIT-tags.md: tag 2.46 holds content other than its Meaning, Where, Uses bullets, in that order")

    def test_reports_a_tag_with_no_meaning(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-tags.md", "- Meaning: Checked against the release notes of Git 2.46.\n", "")
        self.assertErrors(doc_set, "GIT-tags.md: tag 2.46 has no Meaning")

    def test_reports_a_tag_with_an_unknown_where(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-tags.md", "- Where: inline\n", "- Where: prose\n")
        self.assertErrors(doc_set, "GIT-tags.md: tag 2.46 has Where `prose`; use doc, inline or `doc, inline`")

    def test_reports_a_tag_whose_anchor_is_the_h1s(self):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / "GIT-tags.md", "a", encoding="utf-8") as f:
            f.write("\n## git tags\n\n- Meaning: Tags of the git tool.\n- Where: inline\n")
        self.assertErrors(doc_set, "GIT-tags.md: tag git tags has the anchor git-tags, as the H1 does")

    def test_reports_a_tags_field_that_isnt_bullets(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / INDEX_SECTION_FILE, "## Tags\n\n", "## Tags\n\nRelease tags:\n\n")
        self.assertErrors(doc_set, f"{INDEX_SECTION_FILE}: Field Tags holds content other than bullets")

    def test_passes_braces_around_text_that_isnt_a_tag(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", "ref; branch; HEAD; {not a tag}; `{2.43}`\n")
        self.assertPasses(doc_set)

    def test_passes_an_entry_derive_added_naming_a_tag_no_longer_in_the_tags_doc(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "(inline)\n", "(inline)\n- [2.44](GIT-tags.md#244): Gone. (from GIT-03)\n")
        self.assertErrors(
            doc_set,
            f"{CAT_FILE}: Field Tags has `- [2.44](GIT-tags.md#244): Gone. (from GIT-03)`, which derive doesn't write; "
            "edit its source and run derive",
        )

    # The other rules check enforces, each on a copy of the golden doc set.

    def test_passes_ids_in_code_and_in_links_out_of_the_curriculum(self):
        doc_set = self.copy(GOLDEN)
        replace(
            doc_set / REFS_FILE,
            "Stops before history,",
            "Stops before history, `GIT-99`, [GIT-7 notes](https://example.com/GIT-99) and\n\n    GIT-98\n\nthen",
        )
        self.assertPasses(doc_set)

    def test_reports_a_url_encoded_link_target(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-overview.md", "(GIT-02-history.md)", "(GIT%2D02-history.md)")
        self.assertErrors(
            doc_set,
            "GIT-overview.md: link target GIT%2D02-history.md isn't a bare sibling filename or a same-file anchor; "
            "run derive to rewrite it",
        )

    def test_reports_a_prereq_naming_its_own_unit(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "## Prereqs\n\n", "## Prereqs\n\n- GIT-01.01.02\n")
        self.assertErrors(doc_set, f"{REFS_FILE}: Prereq GIT-01.01.02 doesn't come before GIT-01.01.02")

    def test_reports_a_hand_edit_to_a_nav_line(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, f" · Prev [GIT-01.01.01]({SUBSECTION_FILE})", "")
        self.assertErrors(
            doc_set,
            f"{REFS_FILE}: the nav line lacks `· Prev [GIT-01.01.01]({SUBSECTION_FILE})`, "
            "which derive writes; edit its source and run derive",
        )

    def test_reports_a_prev_link_across_a_part_boundary(self):
        self.assertErrors(
            INVALID / "nav-line-across-part",
            f"{ANCESTRY_FILE}: the nav line has `· Prev [GIT-01.02.01](GIT-01.02.01-the-index-as-a-staging-snapshot.md)`, "
            "which derive doesn't write; edit its source and run derive",
        )

    def test_reports_a_hand_edit_to_a_parts_needs(self):
        self.assertErrors(
            INVALID / "needs-edited",
            f"{PART_2_FILE}: Field Needs has `- [GIT-03 Plumbing](GIT-03-plumbing.md)`, which derive doesn't write; "
            "edit its source and run derive",
        )

    def test_reports_needs_written_on_a_part_that_has_none(self):
        # A Field derive doesn't write is placed by the text before it, here the end of Intro.
        self.assertErrors(
            INVALID / "needs-unexpected",
            f"{PART_FILE}: Field Intro has `## Needs - [GIT-02 History](GIT-02-history.md)`, which derive doesn't write; "
            "edit its source and run derive",
        )

    def test_reports_a_hand_edit_to_a_needs_cell(self):
        self.assertErrors(
            INVALID / "needs-cell-edited",
            "index.md: Field Parts lacks `[GIT-01](GIT-01-repository-internals.md)`, which derive writes; edit its source and run derive",
        )

    def test_reports_content_beside_a_nav_line(self):
        for fixture in NAV_LINE_EXTRA:
            with self.subTest(fixture):
                self.assertErrors(
                    INVALID / fixture,
                    f"{REFS_FILE}: has content between its H1 and first Field other than one paragraph, the nav line; "
                    "move it into a Field",
                )

    def test_reports_an_own_code_token_between_backticks_in_two_paragraphs(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", "ref; branch; HEAD; one ` tick\n\nGIT-7\n\nthree `code`\n")
        self.assertErrors(doc_set, f"{REFS_FILE}: GIT-7 isn't an ID: each level is two digits from 01 to 99")

    def test_reports_an_unknown_field(self):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / PART_FILE, "a", encoding="utf-8") as f:
            f.write("\n## Summary\n\nNot a Part Field.\n")
        self.assertErrors(doc_set, f"{PART_FILE}: unknown Field Summary")

    def test_reports_a_repeated_field(self):
        doc_set = self.copy(GOLDEN)
        with open(doc_set / PART_FILE, "a", encoding="utf-8") as f:
            f.write("\n## Intro\n\nA second intro.\n")
        self.assertErrors(doc_set, f"{PART_FILE}: Field Intro appears more than once")

    def test_reports_a_repeated_field_apart_from_its_first_copy_as_repeated(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "index.md", "## Target version", "## Intro\n\nA second intro.\n\n## Target version")
        self.assertErrors(doc_set, "index.md: Field Intro appears more than once")

    def test_reports_a_field_out_of_order(self):
        doc_set = self.copy(GOLDEN)
        overview = doc_set / "GIT-overview.md"
        text = overview.read_text(encoding="utf-8")
        methodology, ordering = text.split("\n## Ordering rationale\n")
        head, methodology = methodology.split("## Methodology\n")
        overview.write_text(f"{head}## Ordering rationale\n{ordering}\n## Methodology\n{methodology}", encoding="utf-8")
        self.assertErrors(doc_set, "GIT-overview.md: Field Methodology is out of order")

    def test_reports_free_content_before_a_notes_field(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-notes.md", "## Build notes", "## Aside\n\nA free H2.\n\n## Build notes")
        self.assertErrors(
            doc_set,
            "GIT-notes.md: Field Build notes comes after free content Aside",
            "GIT-notes.md: Field Open questions comes after free content Aside",
        )

    def test_reports_a_unit_title_with_a_character_that_breaks_links(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "# GIT-01 Repository internals", "# GIT-01 Repository & internals")
        self.assertErrors(doc_set, f"{PART_FILE}: title contains &, which would break a link or table copying it")

    def test_reports_a_curriculum_name_with_a_character_that_breaks_links(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "index.md", "# Git (GIT)", "# Git [core] (GIT)")
        self.assertErrors(doc_set, "index.md: name contains [ ], which would break a link or table copying it")

    def test_reports_a_unit_title_with_an_empty_slug(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / PART_FILE).rename(doc_set / "GIT-01-x.md")
        replace(doc_set / "GIT-01-x.md", "# GIT-01 Repository internals", "# GIT-01 ———")
        self.assertErrors(doc_set, "GIT-01-x.md: title has an empty slug")

    def test_reports_a_subdirectory(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "extra").mkdir()
        self.assertErrors(doc_set, "extra: is a subdirectory; a doc set is flat")

    def test_reports_a_file_outside_the_doc_set(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "todo.txt").write_text("", encoding="utf-8")
        self.assertErrors(doc_set, "todo.txt: isn't a doc set filename")

    def test_reports_two_files_with_one_id(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-01-other.md").write_text("# GIT-01 Other\n\n## Intro\n\nA second Part 1.\n", encoding="utf-8")
        self.assertErrors(doc_set, f"{PART_FILE}: GIT-01 also names GIT-01-other.md")

    def test_reports_a_missing_standard_doc(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-notes.md").unlink()
        self.assertErrors(doc_set, "GIT-notes.md: is missing")

    def test_reports_a_section_with_no_subsection(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / INDEX_SUBSECTION_FILE).unlink()
        self.assertErrors(doc_set, f"{INDEX_SECTION_FILE}: GIT-01.02 has no Subsection")

    def test_reports_an_optional_field_written_as_none(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "## Scope\n", "## Generators\n\nNone\n\n## Scope\n")
        replace(doc_set / "index.md", "## Target version\n\n2.47.1\n", "## Target version\n\nNone\n")
        replace(doc_set / SECTION_FILE, "## Subsections\n", "## Tags\n\nNone\n\n## Subsections\n")
        replace(doc_set / CAT_FILE, "## Scope\n", "## Foundations\n\nnone.\n\n## Scope\n")
        self.assertErrors(
            doc_set,
            *(f"{name}: Optional Field {field} is `{text}`; leave it out when empty"
              for name, field, text in (
                  (REFS_FILE, "Generators", "None"),
                  ("index.md", "Target version", "None"),
                  (SECTION_FILE, "Tags", "None"),
                  (CAT_FILE, "Foundations", "none."),
              )),
        )

    def test_reports_an_id_level_above_99(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-01.01.100-packs.md").write_text("# GIT-01.01.100 Packs\n", encoding="utf-8")
        self.assertErrors(doc_set, "GIT-01.01.100-packs.md: GIT-01.01.100 isn't an ID: each level is two digits from 01 to 99")

    def test_reports_a_part_with_no_section(self):
        doc_set = self.copy(GOLDEN)
        for path in doc_set.glob("GIT-02.*"):
            path.unlink()
        replace(doc_set / REFS_FILE, ", which [GIT-02.01.01 Ancestry](GIT-02.01.01-ancestry.md) covers", "")
        self.assertErrors(doc_set, f"{PART_2_FILE}: GIT-02 has no Section")

    def test_reports_a_doc_set_with_no_part(self):
        doc_set = self.copy(GOLDEN)
        for path in doc_set.glob("GIT-0*.md"):
            path.unlink()
        self.assertErrors(doc_set, "index.md: the doc set has no Part")

    def test_reports_only_the_bad_h1_of_a_unit_with_children(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.02 Objects")
        self.assertErrors(doc_set, f"{SECTION_FILE}: H1 ID GIT-01.02 differs from the filename's ID GIT-01.01")

    def test_reports_a_setext_heading(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "changes it.\n", "changes it.\n---\n")
        self.assertErrors(doc_set, f"{PART_FILE}: has a setext heading, `What a repository holds on disk, before any command that changes it.` over `---`; use an ATX heading")

    def test_passes_a_thematic_break_after_a_blank_line(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "changes it.\n", "changes it.\n\n---\n\nMore.\n")
        result = run("check", doc_set)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_reports_section_generators_with_content_other_than_bullets(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / SECTION_FILE, "## Generators\n\n", "## Generators\n\nThe base facts:\n\n")
        self.assertErrors(doc_set, f"{SECTION_FILE}: Field Generators holds content other than bullets")

    # One fixture per rule #21 names.

    def test_reports_an_abbreviation_defined_twice_with_different_meanings(self):
        self.assertErrors(
            INVALID / "abbreviation-clash",
            "GIT-sources.md: abbreviation man is defined more than once, as "
            "`Git manual pages, version 2.47.1` and `Git manual pages, version 2.46`",
        )

    def test_reports_an_appendix_with_a_tags_prereqs_or_check_field(self):
        self.assertErrors(
            INVALID / "appendix-unit-field",
            *(f"{APPENDIX_FILE}: has a {name} Field, which an Appendix can't: it isn't a unit" for name in ("Tags", "Prereqs", "Check")),
        )

    def test_reports_an_appendix_applying_to_an_unknown_id(self):
        self.assertErrors(INVALID / "appendix-applies-to-unknown", f"{APPENDIX_FILE}: Applies to GIT-02.09 names no Section")

    # The other Appendix rules, each on a copy of the golden doc set.

    def test_reports_an_appendix_applying_to_a_subsection(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / APPENDIX_FILE, "- GIT-02.01\n", "- GIT-02.01\n- GIT-02.01.01\n")
        self.assertErrors(doc_set, f"{APPENDIX_FILE}: Applies to entry `GIT-02.01.01` isn't a Part or Section ID of this Curriculum")

    def test_reports_an_applies_to_that_isnt_bullets(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / APPENDIX_FILE, "## Applies to\n\n", "## Applies to\n\nThese units:\n\n")
        self.assertErrors(doc_set, f"{APPENDIX_FILE}: Field Applies to holds content other than bullets")

    def test_reports_an_appendix_error_beside_a_link_error(self):
        doc_set = self.copy(INVALID / "abbreviation-clash")
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", "ref; branch; HEAD; GIT-01.09.09\n")
        self.assertErrors(
            doc_set,
            "GIT-sources.md: abbreviation man is defined more than once, as "
            "`Git manual pages, version 2.47.1` and `Git manual pages, version 2.46`",
            f"{REFS_FILE}: GIT-01.09.09 names no unit",
        )

    def test_reports_an_appendix_without_a_purpose(self):
        doc_set = self.copy(GOLDEN)
        text = (doc_set / APPENDIX_FILE).read_text(encoding="utf-8")
        start, end = text.index("## Purpose"), text.index("## Applies to")
        (doc_set / APPENDIX_FILE).write_text(text[:start] + text[end:], encoding="utf-8")
        self.assertErrors(doc_set, f"{APPENDIX_FILE}: required Field Purpose is missing")

    def test_reports_a_subsection_linking_an_appendix(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", f"ref; branch; HEAD; [coverage]({APPENDIX_FILE})\n")
        self.assertErrors(
            doc_set,
            f"{REFS_FILE}: link [coverage]({APPENDIX_FILE}) names no unit or tag; write the unit's bare ID or the tag's marker instead",
        )

    def test_reports_an_appendix_with_a_bad_h1(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-appendix-glossary.md").write_text("# Glossary\n", encoding="utf-8")
        self.assertErrors(doc_set, "GIT-appendix-glossary.md: H1 `# Glossary` isn't `# GIT Appendix: <title>`")

    def test_reports_a_unit_whose_parent_is_missing(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / SECTION_FILE).unlink()
        self.assertErrors(
            doc_set,
            f"{SUBSECTION_FILE}: GIT-01.01.01 has no Section GIT-01.01",
            f"{REFS_FILE}: GIT-01.01.02 has no Section GIT-01.01",
        )

    def test_passes_a_field_inside_an_html_comment(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "changes it.\n", "changes it.\n\n<!--\n## Intro\n\nAn older intro.\n-->\n")
        self.assertPasses(doc_set)

    def test_passes_a_setext_heading_inside_a_list_item(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "changes it.\n", "changes it.\n\n- item\n\n  More text\n  ---\n")
        self.assertPasses(doc_set)

    def test_reports_a_missing_marksman_file(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / ".marksman.toml").unlink()
        self.assertErrors(doc_set, ".marksman.toml: is missing")

    def test_reports_a_marksman_file_that_isnt_empty(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / ".marksman.toml").write_text("[core]\n", encoding="utf-8")
        self.assertErrors(doc_set, ".marksman.toml: isn't empty")

    def test_reports_an_id_with_non_ascii_digits(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "# GIT-01 ", "# GIT-０１ ")
        self.assertErrors(doc_set, f"{PART_FILE}: H1 `# GIT-０１ Repository internals` isn't `# <ID> <title>`")

    def test_reports_a_doc_that_isnt_utf_8(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-overview.md").write_bytes(b"# GIT Overview \xff\n")
        self.assertErrors(doc_set, "GIT-overview.md: isn't valid UTF-8")

    def test_reports_a_doc_with_a_byte_order_mark(self):
        doc_set = self.copy(GOLDEN)
        path = doc_set / "GIT-overview.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertErrors(doc_set, "GIT-overview.md: starts with a byte order mark; save it as UTF-8 without one")

    def test_reports_a_multi_line_format_version_on_one_line(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "index.md", "## Format version\n\n2\n", "## Format version\n\n2\n\nSet by split.\n")
        self.assertErrors(
            doc_set, "index.md: Format version is '2\\n\\nSet by split.', but this script reads Format version 2"
        )


class Derive(TempDirTestCase):
    def assertStops(self, fixture, line):
        """derive exits 1 with this error and leaves the doc set untouched."""
        doc_set = self.copy(fixture)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(line, result.stderr.splitlines())
        self.assertEqual(filecmp.dircmp(doc_set, fixture).diff_files, [])

    def test_stops_when_the_format_version_differs(self):
        self.assertStops(
            INVALID / "format-version-mismatch",
            "derive: index.md: Format version is 1, but this script reads Format version 2",
        )

    def test_stops_when_the_format_version_is_missing(self):
        self.assertStops(
            INVALID / "format-version-missing",
            "derive: index.md: Format version is missing; this script reads Format version 2. "
            "Restore it from the history of index.md, such as `git log -p index.md`",
        )

    def test_stops_on_an_error_check_reports(self):
        self.assertStops(INVALID / "field-missing", f"derive: {SUBSECTION_FILE}: required Field Goal is missing")

    def test_stops_on_a_link_error(self):
        self.assertStops(INVALID / "id-unknown", f"derive: {REFS_FILE}: GIT-09.01 names no unit")

    def test_links_a_bare_id_and_refreshes_a_link_it_wrote(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_2_FILE, "[GIT-01.01 Objects](GIT-01.01-objects.md)", "[GIT-01.01 Old title](GIT-01.01-objects.md)")
        replace(doc_set / "GIT-notes.md", "None so far.", "None so far, beyond GIT-01.02.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(filecmp.cmp(doc_set / PART_2_FILE, GOLDEN / PART_2_FILE, shallow=False))
        self.assertIn(
            f"None so far, beyond [GIT-01.02 The index]({INDEX_SECTION_FILE}).\n",
            (doc_set / "GIT-notes.md").read_text(encoding="utf-8"),
        )
        self.assertPasses(doc_set)

    def test_links_an_id_in_braces_and_keeps_the_braces(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-notes.md", "None so far.", "None so far {GIT-01.02}.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            f"None so far {{[GIT-01.02 The index]({INDEX_SECTION_FILE})}}.\n",
            (doc_set / "GIT-notes.md").read_text(encoding="utf-8"),
        )
        self.assertPasses(doc_set)

    def test_links_an_id_after_a_code_block_in_the_same_field(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-notes.md", "None so far.", "None so far.\n\n```text\nlog\n```\n\nSee GIT-01.02.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("See [GIT-01.02 The index](GIT-01.02-the-index.md).\n", (doc_set / "GIT-notes.md").read_text(encoding="utf-8"))

    def test_leaves_ids_outside_prose_unlinked(self):
        doc_set = self.copy(GOLDEN)
        outside = (
            "None so far.\n\n"
            "[see [x] GIT-01.01](https://example.com), [GIT-01.01 ref][r] and [GIT-01.01 p](https://example.com/a_(b)).\n\n"
            "[r]: https://example.com\n\n"
            "    GIT-01.01\n    GIT-01.02\n\n"
            "<div>\nGIT-01.01\n</div>\n"
        )
        replace(doc_set / "GIT-notes.md", "None so far.\n", outside)
        before = (doc_set / "GIT-notes.md").read_bytes()
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((doc_set / "GIT-notes.md").read_bytes(), before)
        self.assertPasses(doc_set)

    def test_keeps_a_code_span_from_pairing_a_backtick_in_an_earlier_paragraph(self):
        doc_set = self.copy(GOLDEN)
        concepts = "ref; branch; HEAD\n\nA lone ` backtick here.\n\nSee `GIT-01.01.01` literally.\n"
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", concepts)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(concepts, (doc_set / REFS_FILE).read_text(encoding="utf-8"))

    def test_links_an_id_between_backticks_in_two_list_items(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "ref; branch; HEAD\n", "- one `tick\n- two GIT-01.01.01 here\n- three `code`\n")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"- two [GIT-01.01.01 {SUBSECTION_TITLE}]({SUBSECTION_FILE}) here\n", (doc_set / REFS_FILE).read_text(encoding="utf-8"))

    def test_links_a_hand_added_tag_marker_and_lists_it_in_the_units_tags(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / REFS_FILE, "Stops before history,", "Checked against {2.43}. Stops before history,")
        replace(doc_set / "GIT-notes.md", "None so far.", "None so far, beyond {2.43}.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        refs = (doc_set / REFS_FILE).read_text(encoding="utf-8")
        self.assertIn("Checked against [2.43](#tags). Stops before history,", refs)
        self.assertIn(
            "  - A commit names one tree and its parent commits.\n\n"
            "## Tags\n\n- [2.43](GIT-tags.md#243): Checked against the release notes of Git 2.43. (inline)\n\n## Goal\n",
            refs,
        )
        self.assertIn("None so far, beyond [2.43](GIT-tags.md#243).", (doc_set / "GIT-notes.md").read_text(encoding="utf-8"))
        self.assertIn("## 2.43\n\n- Meaning: Checked against the release notes of Git 2.43.\n- Where: doc, inline\n- Uses: 2\n",
                      (doc_set / "GIT-tags.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_keeps_a_tag_link_in_a_code_span_when_copying_a_goal(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "as checked against [2.46](#tags).", "as checked against [2.46](#tags), not `[2.46](#tags)`.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "as checked against [2.46](GIT-tags.md#246), not `[2.46](#tags)`.\n",
            (doc_set / "GIT-03.01-reading-objects.md").read_text(encoding="utf-8"),
        )

    def test_drops_a_tag_its_part_no_longer_carries(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-03-plumbing.md", "## Tags\n\n- [Optional](GIT-tags.md#optional): No unit outside it depends on it, so a learner may skip it.\n\n", "")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "## Tags\n\n- [2.46](GIT-tags.md#246): Checked against the release notes of Git 2.46. (inline)\n\n## Goal",
            (doc_set / CAT_FILE).read_text(encoding="utf-8"),
        )
        self.assertIn("- Synthesis: 1\n- Optional: 0\n", (doc_set / "index.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_drops_a_tag_whose_marker_was_removed(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "by its ID, as checked against [2.46](#tags).", "by its ID.")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[2.46]", (doc_set / CAT_FILE).read_text(encoding="utf-8"))
        self.assertIn("## 2.46\n\n- Meaning: Checked against the release notes of Git 2.46.\n- Where: inline\n- Uses: 0\n",
                      (doc_set / "GIT-tags.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_keeps_an_own_tag_its_part_also_carries(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "skip it. (from GIT-03)\n", "skip it.\n")
        replace(doc_set / "GIT-03-plumbing.md", "## Tags\n\n- [Optional](GIT-tags.md#optional): No unit outside it depends on it, so a learner may skip it.\n\n", "")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("so a learner may skip it.\n- [2.46]", (doc_set / CAT_FILE).read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_drops_a_standard_tag_no_unit_carries_any_more(self):
        doc_set = self.copy(GOLDEN)
        synthesis = "- [Synthesis](GIT-tags.md#synthesis): Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own."
        replace(doc_set / ANCESTRY_FILE, f"## Tags\n\n{synthesis}\n\n", "")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("## Tags", (doc_set / ANCESTRY_FILE).read_text(encoding="utf-8"))
        self.assertTrue((doc_set / "GIT-tags.md").read_text(encoding="utf-8").startswith("# GIT Tags\n\n## Optional\n"))
        self.assertIn("- Synthesis: 0\n- Optional: 1\n", (doc_set / "index.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_copies_an_edited_meaning_into_every_tags_field(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / "GIT-tags.md", "- Meaning: Checked against the release notes of Git 2.43.", "- Meaning: Checked against Git 2.43.")
        stale = "Field Tags has `the release notes of`, which derive doesn't write; edit its source and run derive"
        self.assertErrors(doc_set, f"{INDEX_SECTION_FILE}: {stale}", f"{INDEX_SUBSECTION_FILE}: {stale}")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in (INDEX_SECTION_FILE, INDEX_SUBSECTION_FILE):
            with self.subTest(name):
                self.assertIn("- [2.43](GIT-tags.md#243): Checked against Git 2.43.", (doc_set / name).read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_stops_on_content_beside_a_nav_line(self):
        for fixture in NAV_LINE_EXTRA:
            with self.subTest(fixture):
                self.assertStops(
                    INVALID / fixture,
                    f"derive: {REFS_FILE}: has content between its H1 and first Field other than one paragraph, the nav line; "
                    "move it into a Field",
                )

    def test_refreshes_a_unit_link_whose_target_is_stale(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_2_FILE, "[GIT-01.01 Objects](GIT-01.01-objects.md)", "[GIT-01.01 Objects](GIT-01.01-old.md)")
        check = run("check", doc_set)
        self.assertIn(
            f"{PART_2_FILE}: link target GIT-01.01-old.md names no file in the doc set; run derive to rewrite it",
            check.stdout.splitlines(),
        )
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [])

    def test_links_an_appendix_with_no_applies_to_from_the_index_only(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-appendix-glossary.md").write_text(
            "# GIT Appendix: Glossary\n\n## Purpose\n\nTerms the units of GIT-01 share.\n", encoding="utf-8"
        )
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "- [Notes](GIT-notes.md)\n"
            "- [Appendix: Glossary](GIT-appendix-glossary.md): Terms the units of "
            "[GIT-01 Repository internals](GIT-01-repository-internals.md) share.\n"
            f"- [Appendix: Manual coverage]({APPENDIX_FILE}): Which manual pages",
            (doc_set / "index.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(sorted(filecmp.dircmp(doc_set, GOLDEN).diff_files), ["index.md"])
        self.assertPasses(doc_set)

    def test_drops_the_appendices_field_of_a_section_applies_to_no_longer_names(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / APPENDIX_FILE, "- GIT-02.01\n", "")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("## Appendices", (doc_set / COMMIT_GRAPH_FILE).read_text(encoding="utf-8"))
        self.assertIn("## Appendices", (doc_set / PART_FILE).read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_twice_gives_no_diff(self):
        doc_set = self.copy(GOLDEN)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [])

    def test_twice_after_hand_edits_gives_no_diff(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.01 Object store")
        replace(doc_set / "GIT-notes.md", "None so far.", "None so far, beyond GIT-01.02 and {2.43}.")
        self.assertEqual(run("derive", doc_set).returncode, 0)
        once = {name: (doc_set / name).read_bytes() for name in tree(doc_set)}
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({name: (doc_set / name).read_bytes() for name in tree(doc_set)}, once)

    def test_renames_a_unit_whose_title_changed_and_relinks_it(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.01 Object store")
        check = run("check", doc_set)
        self.assertEqual(check.returncode, 1)
        self.assertIn(
            f"{SECTION_FILE}: filename should be GIT-01.01-object-store.md, from its title; run derive to rename it",
            check.stdout.splitlines(),
        )
        self.assertIn(
            f"{PART_FILE}: Field Sections has `Objects]({SECTION_FILE})` where derive writes "
            f"`Object store]({SECTION_FILE})`; run derive to copy the new title",
            check.stdout.splitlines(),
        )
        self.assertNotIn("edit its source", check.stdout)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((doc_set / SECTION_FILE).exists())
        self.assertIn("- [GIT-01.01 Object store](GIT-01.01-object-store.md)\n", (doc_set / PART_FILE).read_text(encoding="utf-8"))
        self.assertIn("- Section: [GIT-01.01 Object store](GIT-01.01-object-store.md)\n", (doc_set / REFS_FILE).read_text(encoding="utf-8"))
        self.assertIn(" · [GIT-01.01](GIT-01.01-object-store.md) · ", (doc_set / REFS_FILE).read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_reports_a_hand_edit_to_derived_content_beside_a_rename(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "# GIT-03.01.01 cat-file", "# GIT-03.01.01 Reading with cat-file")
        replace(doc_set / "GIT-tags.md", "- Where: inline\n- Uses: 1\n", "- Where: inline\n- Uses: 9\n")
        result = run("check", doc_set)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            f"{CAT_FILE}: filename should be GIT-03.01.01-reading-with-cat-file.md, from its title; run derive to rename it",
            result.stdout.splitlines(),
        )
        self.assertIn("GIT-tags.md: tag 2.46 has `9` where derive writes `1`; edit its source and run derive", result.stdout.splitlines())

    def test_reports_a_hand_edited_copy_of_a_renamed_units_title(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.01 Object store")
        replace(doc_set / "GIT-02-history.md", f"Objects]({SECTION_FILE}).", f"Object model]({SECTION_FILE}).")
        result = run("check", doc_set)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            f"GIT-02-history.md: Field Intro has `model]({SECTION_FILE}).` where derive writes "
            f"`store]({SECTION_FILE}).`; edit its source and run derive",
            result.stdout.splitlines(),
        )

    def test_renames_a_misnamed_file_back_to_its_titles_filename(self):
        doc_set = self.copy(INVALID / "filename-slug")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [])
        self.assertEqual(tree(doc_set), tree(GOLDEN))

    def test_relinks_prose_naming_a_renamed_unit(self):
        doc_set = self.copy(GOLDEN)
        old, new = "GIT-02.01.01-ancestry.md", "GIT-02.01.01-ancestry-and-reachability.md"
        replace(doc_set / ANCESTRY_FILE, "# GIT-02.01.01 Ancestry", "# GIT-02.01.01 Ancestry and reachability")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in doc_set.glob("GIT-02.01.01-*")), [new])
        refs = (doc_set / REFS_FILE).read_text(encoding="utf-8")
        self.assertIn(f"which [GIT-02.01.01 Ancestry and reachability]({new}) covers.", refs)
        self.assertNotIn(old, "".join((doc_set / name).read_text(encoding="utf-8") for name in tree(doc_set)))
        self.assertPasses(doc_set)

    def test_keeps_front_matter_on_a_doc_it_renames_and_rewrites(self):
        doc_set = self.copy(GOLDEN)
        front = "---\naliases: [Ancestry, GIT-01.01]\n---\n\n"
        (doc_set / ANCESTRY_FILE).write_text(front + (doc_set / ANCESTRY_FILE).read_text(encoding="utf-8"), encoding="utf-8")
        self.assertPasses(doc_set)
        replace(doc_set / ANCESTRY_FILE, "# GIT-02.01.01 Ancestry", "# GIT-02.01.01 Reachability")
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.01 Object store")  # changes its Prereqs' copies
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (doc_set / "GIT-02.01.01-reachability.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith(front + "# GIT-02.01.01 Reachability\n"), text[:200])
        self.assertPasses(doc_set)

    def test_renames_nothing_when_another_error_stops_it(self):
        doc_set = self.copy(INVALID / "id-unknown")
        replace(doc_set / SECTION_FILE, "# GIT-01.01 Objects", "# GIT-01.01 Object store")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"derive: {REFS_FILE}: GIT-09.01 names no unit", result.stderr.splitlines())
        self.assertTrue((doc_set / SECTION_FILE).exists())

    def test_lists_the_part_of_a_new_prereq_in_needs(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / CAT_FILE, "## Prereqs\n\n- [GIT-01.01.01", "## Prereqs\n\n- GIT-02.01.01\n- [GIT-01.01.01")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "## Needs\n\n- [GIT-01 Repository internals](GIT-01-repository-internals.md)\n- [GIT-02 History](GIT-02-history.md)\n\n## Tags\n",
            (doc_set / PLUMBING_FILE).read_text(encoding="utf-8"),
        )
        self.assertIn(
            "| [GIT-03](GIT-03-plumbing.md) | Plumbing | 1 | 1 | [GIT-01](GIT-01-repository-internals.md), [GIT-02](GIT-02-history.md) |\n",
            (doc_set / "index.md").read_text(encoding="utf-8"),
        )
        self.assertPasses(doc_set)

    def test_drops_needs_when_no_prereq_lands_in_another_part(self):
        doc_set = self.copy(GOLDEN)
        text = (doc_set / CAT_FILE).read_text(encoding="utf-8")
        start, end = text.index("## Prereqs\n"), text.index("## Check\n")
        (doc_set / CAT_FILE).write_text(text[:start] + "## Prereqs\n\nNone\n\n" + text[end:], encoding="utf-8")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("## Needs", (doc_set / PLUMBING_FILE).read_text(encoding="utf-8"))
        self.assertIn("| [GIT-03](GIT-03-plumbing.md) | Plumbing | 1 | 1 | |\n", (doc_set / "index.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def test_adds_no_needs_for_a_prereq_in_the_same_part(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / INDEX_SUBSECTION_FILE, "## Prereqs\n\n", "## Prereqs\n\n- GIT-01.01.02\n")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [INDEX_SUBSECTION_FILE])
        self.assertPasses(doc_set)

    def test_copies_a_retitled_part_into_needs(self):
        doc_set = self.copy(GOLDEN)
        replace(doc_set / PART_FILE, "# GIT-01 Repository internals", "# GIT-01 Object database")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in (PART_2_FILE, PLUMBING_FILE):
            with self.subTest(name):
                self.assertIn(
                    "## Needs\n\n- [GIT-01 Object database](GIT-01-object-database.md)\n", (doc_set / name).read_text(encoding="utf-8")
                )
        self.assertIn("| History | 1 | 1 | [GIT-01](GIT-01-object-database.md) |\n", (doc_set / "index.md").read_text(encoding="utf-8"))
        self.assertPasses(doc_set)

    def write_math(self, name="math"):
        """A second Curriculum beside the copied doc set, holding the Subsection its Prereq names."""
        math = self.tmp / name
        math.mkdir()
        (math / "index.md").write_text("# Mathematics (MATH)\n", encoding="utf-8")
        (math / "MATH-03.01.02-reachability.md").write_text(
            "# MATH-03.01.02 Reachability\n\n## Goal\n\nA vertex reaches another when a path joins them, "
            "as in [MATH-03.01.01 Paths](MATH-03.01.01-paths.md).\n",
            encoding="utf-8",
        )

    def test_copies_a_prereq_from_another_curriculum_beside_the_doc_set(self):
        doc_set = self.copy(GOLDEN)
        self.write_math()
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "- MATH-03.01.02 Reachability: A vertex reaches another when a path joins them, as in MATH-03.01.01 Paths.\n",
            (doc_set / ANCESTRY_FILE).read_text(encoding="utf-8"),
        )
        self.assertPasses(doc_set)

    def test_keeps_a_prereq_whose_code_two_curricula_beside_it_share(self):
        doc_set = self.copy(GOLDEN)
        self.write_math("math")
        self.write_math("math-old")
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [])

    def test_leaves_alone_docs_with_nothing_to_derive(self):
        doc_set = self.copy(GOLDEN)
        overview = doc_set / "GIT-overview.md"
        overview.write_text(overview.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        appendix = doc_set / APPENDIX_FILE
        appendix.write_text("---\naliases: [Coverage]\n---\n\n" + appendix.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        before = {name: (doc_set / name).read_bytes() for name in tree(doc_set)}
        check = run("check", doc_set)
        self.assertEqual((check.returncode, check.stdout), (0, ""))
        derive = run("derive", doc_set)
        self.assertEqual(derive.returncode, 0, derive.stderr)
        self.assertEqual({name: (doc_set / name).read_bytes() for name in tree(doc_set)}, before)


if __name__ == "__main__":
    unittest.main()
