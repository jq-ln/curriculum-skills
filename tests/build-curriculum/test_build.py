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
MINIMAL = FIXTURES / "minimal"
INVALID = FIXTURES / "check"
SUBSECTION_SLUG = "content-addressed-objects-blobs-trees-commits-and-the-naive"
SUBSECTION = f"GIT-01.01.01-{SUBSECTION_SLUG}.md"  # the fixtures' one Subsection


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


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def copy(self, src):
        dst = self.tmp / "doc-set"
        shutil.copytree(src, dst)
        return dst


class SplitThenDerive(TempDirTestCase):
    def test_reproduces_the_golden_doc_set_byte_for_byte(self):
        out = self.tmp / "git"
        split = run("split", MINIMAL / "draft", out)
        self.assertEqual(split.returncode, 0, split.stderr)
        derive = run("derive", out)
        self.assertEqual(derive.returncode, 0, derive.stderr)

        golden = MINIMAL / "golden"
        self.assertEqual(tree(out), tree(golden))
        for name in tree(golden):
            with self.subTest(file=name):
                self.assertTrue(
                    filecmp.cmp(out / name, golden / name, shallow=False),
                    f"{name} differs from the golden copy",
                )


class Check(TempDirTestCase):
    def assertErrors(self, fixture, *lines):
        """check exits 1 and prints exactly these error lines, in any order."""
        result = run("check", INVALID / fixture)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertCountEqual(result.stdout.splitlines(), lines)

    def test_passes_the_golden_doc_set(self):
        result = run("check", MINIMAL / "golden")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_reports_a_missing_format_version(self):
        self.assertErrors(
            "format-version-missing",
            "index.md: Format version is missing; this script reads Format version 1. "
            "Restore it from the history of index.md, such as `git log -p index.md`",
        )

    def test_names_both_numbers_when_the_format_version_differs(self):
        self.assertErrors(
            "format-version-mismatch",
            "index.md: Format version is 2, but this script reads Format version 1",
        )

    def test_reports_a_missing_required_field(self):
        self.assertErrors("field-missing", f"{SUBSECTION}: required Field Goal is missing")

    def test_reports_an_h1_id_that_differs_from_the_filename(self):
        self.assertErrors(
            "id-mismatch",
            f"{SUBSECTION}: H1 ID GIT-01.01.02 differs from the filename's ID GIT-01.01.01",
        )

    def test_reports_an_id_with_an_unpadded_level(self):
        self.assertErrors(
            "id-malformed",
            f"GIT-01.01.1-{SUBSECTION_SLUG}.md: GIT-01.01.1 isn't an ID: each level is two digits from 01 to 99",
        )

    def test_reports_a_filename_whose_slug_differs_from_the_title(self):
        self.assertErrors(
            "filename-slug",
            f"GIT-01.01.01-objects.md: filename should be {SUBSECTION}, from its title",
        )

    def test_reports_a_hand_edit_to_derived_content(self):
        self.assertErrors(
            "context-edited",
            f"{SUBSECTION}: derived content differs from what derive writes; edit its source and run derive",
        )



class Derive(TempDirTestCase):
    def assertStops(self, fixture, line):
        """derive exits 1 with this error and leaves the doc set untouched."""
        doc_set = self.copy(INVALID / fixture)
        result = run("derive", doc_set)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(line, result.stderr.splitlines())
        self.assertEqual(filecmp.dircmp(doc_set, INVALID / fixture).diff_files, [])

    def test_stops_when_the_format_version_differs(self):
        self.assertStops(
            "format-version-mismatch",
            "derive: index.md: Format version is 2, but this script reads Format version 1",
        )

    def test_stops_when_the_format_version_is_missing(self):
        self.assertStops(
            "format-version-missing",
            "derive: index.md: Format version is missing; this script reads Format version 1. "
            "Restore it from the history of index.md, such as `git log -p index.md`",
        )


if __name__ == "__main__":
    unittest.main()
