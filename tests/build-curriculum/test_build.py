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

    def test_stops_on_an_output_path_that_is_a_file(self):
        out = self.tmp / "git"
        out.write_text("", encoding="utf-8")
        result = run("split", DRAFT, out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stderr.splitlines(), [f"split: {out}: already exists and isn't a directory"])


class Check(TempDirTestCase):
    def assertErrors(self, doc_set, *lines):
        """check exits 1 and prints exactly these error lines, in any order."""
        result = run("check", doc_set)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertCountEqual(result.stdout.splitlines(), lines)

    def test_passes_the_golden_doc_set(self):
        result = run("check", GOLDEN)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    # One fixture per rule #18 names.

    def test_reports_a_missing_format_version(self):
        self.assertErrors(
            INVALID / "format-version-missing",
            "index.md: Format version is missing; this script reads Format version 1. "
            "Restore it from the history of index.md, such as `git log -p index.md`",
        )

    def test_names_both_numbers_when_the_format_version_differs(self):
        self.assertErrors(
            INVALID / "format-version-mismatch",
            "index.md: Format version is 2, but this script reads Format version 1",
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
            f"GIT-01.01.01-objects.md: filename should be {SUBSECTION_FILE}, from its title",
        )

    def test_reports_a_hand_edit_to_derived_content(self):
        self.assertErrors(
            INVALID / "context-edited",
            f"{SUBSECTION_FILE}: derived content differs from what derive writes; edit its source and run derive",
        )

    # One fixture per rule #19 names.

    def test_reports_an_own_code_id_naming_no_unit(self):
        self.assertErrors(INVALID / "id-unknown", f"{REFS_FILE}: GIT-09.01 names no unit")

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
            "GIT-notes.md: link [the overview](GIT-overview.md) names no unit; write the unit's bare ID instead",
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
        replace(doc_set / ANCESTRY_FILE, " · Prev [GIT-01.02.01](GIT-01.02.01-the-index-as-a-staging-snapshot.md)", "")
        self.assertErrors(
            doc_set, f"{ANCESTRY_FILE}: derived content differs from what derive writes; edit its source and run derive"
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
        self.assertErrors(doc_set, "GIT-notes.md: Field Build notes comes after free content Aside")

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

    def test_passes_an_appendix(self):
        doc_set = self.copy(GOLDEN)
        (doc_set / "GIT-appendix-glossary.md").write_text(
            "# GIT Appendix: Glossary\n\n## Purpose\n\nTerms the units share.\n", encoding="utf-8"
        )
        result = run("check", doc_set)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

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
        replace(doc_set / "index.md", "## Format version\n\n1\n", "## Format version\n\n1\n\nSet by split.\n")
        self.assertErrors(
            doc_set, "index.md: Format version is '1\\n\\nSet by split.', but this script reads Format version 1"
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
            "derive: index.md: Format version is 2, but this script reads Format version 1",
        )

    def test_stops_when_the_format_version_is_missing(self):
        self.assertStops(
            INVALID / "format-version-missing",
            "derive: index.md: Format version is missing; this script reads Format version 1. "
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

    def test_twice_gives_no_diff(self):
        doc_set = self.copy(GOLDEN)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(filecmp.dircmp(doc_set, GOLDEN).diff_files, [])

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
        appendix = doc_set / "GIT-appendix-glossary.md"
        appendix.write_text("---\naliases: [Glossary]\n---\n\n# GIT Appendix: Glossary\n", encoding="utf-8")
        before = {name: (doc_set / name).read_bytes() for name in tree(doc_set)}
        check = run("check", doc_set)
        self.assertEqual((check.returncode, check.stdout), (0, ""))
        derive = run("derive", doc_set)
        self.assertEqual(derive.returncode, 0, derive.stderr)
        self.assertEqual({name: (doc_set / name).read_bytes() for name in tree(doc_set)}, before)


if __name__ == "__main__":
    unittest.main()
