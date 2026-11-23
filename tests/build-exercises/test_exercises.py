"""Tests for skills/build-exercises/scripts/exercises.py, driven only through its CLI."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "build-exercises" / "scripts" / "exercises.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CURRICULUMS = FIXTURES / "curriculums"  # GIT, whose GIT-02.01.01 has a Prereq in MATH, and MATH
GOLDEN = FIXTURES / "context"


def run(*args, cwd=None, script=SCRIPT):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )


def golden(name, curriculums=CURRICULUMS):
    """The golden output, with {curriculums} standing for the resolved Curriculums directory the run searched."""
    return (GOLDEN / f"{name}.txt").read_text(encoding="utf-8").replace("{curriculums}", str(Path(curriculums).resolve()))


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class Context(TempDirTestCase):
    def test_prints_the_anchor_and_its_prereq_closure(self):
        result = run("context", "GIT-01.02.01", "--curriculums", CURRICULUMS)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, golden("plain"), ""))

    def test_follows_a_prereq_into_another_curriculum_and_its_own_prereqs(self):
        result = run("context", "GIT-02.01.01", "--curriculums", CURRICULUMS)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, golden("cross-curriculum"), ""))

    def test_reports_a_prereq_whose_curriculum_is_missing_and_carries_on(self):
        shutil.copytree(CURRICULUMS / "git", self.tmp / "git")
        result = run("context", "GIT-02.01.01", "--curriculums", self.tmp)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, golden("missing", self.tmp), ""))

    def test_reads_the_curriculums_in_the_working_directory_by_default(self):
        result = run("context", "GIT-01.02.01", cwd=CURRICULUMS)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, golden("plain"), ""))

    def test_reports_a_prereq_whose_code_two_curriculums_share(self):
        for name in ("git", "math"):
            shutil.copytree(CURRICULUMS / name, self.tmp / name)
        shutil.copytree(CURRICULUMS / "math", self.tmp / "math-old")
        result = run("context", "GIT-02.01.01", "--curriculums", self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                "## MATH-03.01.02\n\n"
                f"Unresolved: several Curriculums in {self.tmp.resolve()} have code MATH: math, math-old\n"
            ),
            result.stdout,
        )

    def test_reports_a_prereq_whose_curriculum_doesnt_load(self):
        for name in ("git", "math"):
            shutil.copytree(CURRICULUMS / name, self.tmp / name)
        (self.tmp / "math" / ".marksman.toml").unlink()
        result = run("context", "GIT-02.01.01", "--curriculums", self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.endswith("## MATH-03.01.02\n\nUnresolved: MATH doesn't load; run build.py check on math\n"),
            result.stdout,
        )

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads a file whatever its mode")
    def test_reports_a_prereq_whose_curriculum_has_an_unreadable_file(self):
        for name in ("git", "math"):
            shutil.copytree(CURRICULUMS / name, self.tmp / name)
        unreadable = next((self.tmp / "math").glob("MATH-03.01.01-*.md"))
        unreadable.chmod(0)
        result = run("context", "GIT-02.01.01", "--curriculums", self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.endswith("## MATH-03.01.02\n\nUnresolved: MATH doesn't load; run build.py check on math\n"),
            result.stdout,
        )

    def test_reports_a_prereq_naming_no_subsection_of_its_curriculum(self):
        for name in ("git", "math"):
            shutil.copytree(CURRICULUMS / name, self.tmp / name)
        for path in (self.tmp / "math").glob("MATH-03.01.02-*.md"):
            path.unlink()
        result = run("context", "GIT-02.01.01", "--curriculums", self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("## MATH-03.01.02\n\nUnresolved: names no Subsection in MATH\n"), result.stdout)

    def test_stops_on_an_id_that_isnt_a_subsection(self):
        for token, message in [
            ("GIT-01.02", "context: GIT-01.02 isn't a Subsection ID\n"),
            ("git", "context: git isn't an ID\n"),
            ("GIT-01.02.09", "context: GIT-01.02.09 names no Subsection in git\n"),
        ]:
            with self.subTest(token):
                result = run("context", token, "--curriculums", CURRICULUMS)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))

    def test_stops_when_no_curriculum_has_the_ids_code(self):
        result = run("context", "RUST-01.01.01", "--curriculums", CURRICULUMS)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (1, "", f"context: no Curriculum in {CURRICULUMS} has code RUST\n"),
        )

    def test_stops_when_the_anchors_curriculum_doesnt_load(self):
        shutil.copytree(CURRICULUMS / "git", self.tmp / "git")
        (self.tmp / "git" / ".marksman.toml").unlink()
        result = run("context", "GIT-01.02.01", "--curriculums", self.tmp)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", "context: .marksman.toml: is missing\n"))


class Existing(TempDirTestCase):
    def workspace(self, *names):
        """A Practice workspace in the temp dir holding an Exercise at each <CODE>/<name>."""
        practice = self.tmp / "practice"
        practice.mkdir()
        for name in names:
            (practice / name).mkdir(parents=True)
            (practice / name / "EXERCISE.md").write_text("# An Exercise\n", encoding="utf-8")
        return practice

    def test_an_anchor_with_no_exercises_starts_at_01(self):
        practice = self.workspace()
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "None\nNext: 01\n", ""))

    def test_next_follows_the_highest_number_and_never_fills_a_gap(self):
        practice = self.workspace("GIT/GIT-01.02.01-03-amend-a-snapshot", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "GIT-01.02.01-01-stage-one-file\nGIT-01.02.01-03-amend-a-snapshot\nNext: 04\n", ""),
        )

    def test_counts_an_exercise_with_an_empty_slug(self):
        practice = self.workspace("GIT/GIT-01.02.01-01-")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "GIT-01.02.01-01-\nNext: 02\n", ""))

    def test_skips_another_subsections_exercises(self):
        practice = self.workspace("GIT/GIT-01.01.01-04-hash-a-blob", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", ""))

    def test_skips_exercises_in_another_curriculums_directory(self):
        practice = self.workspace("MATH/GIT-01.02.01-05-misfiled", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", ""))

    def test_reads_practice_in_the_curriculums_directory_by_default(self):
        self.workspace("GIT/GIT-01.02.01-01-stage-one-file")
        for args, cwd in [(["--curriculums", self.tmp], None), ([], self.tmp)]:
            with self.subTest(args=args):
                result = run("existing", "GIT-01.02.01", *args, cwd=cwd)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", "")
                )

    def test_stops_on_an_id_that_isnt_a_subsection(self):
        for token, message in [
            ("GIT-01.02", "existing: GIT-01.02 isn't a Subsection ID\n"),
            ("git", "existing: git isn't an ID\n"),
        ]:
            with self.subTest(token):
                result = run("existing", token, "--practice", self.tmp)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))


def exercise_md(anchor, title, code="GIT"):
    """An EXERCISE.md whose anchor record names this anchor."""
    return (
        "# Stage one file\n\n"
        f"- Curriculum: {code}\n"
        f"- Anchor: {anchor}\n"
        f"- Anchor title: {title}\n"
        "- Target version: 2.47\n\n"
        "## Task\n\nStage `a.txt` and nothing else.\n"
    )


class Renumber(TempDirTestCase):
    def workspace(self, exercises):
        """A Practice workspace holding GIT/<name>/EXERCISE.md for each name, with the text given, or none for None."""
        practice = self.tmp / "practice"
        for name, text in exercises.items():
            (practice / "GIT" / name).mkdir(parents=True)
            if text is not None:
                (practice / "GIT" / name / "EXERCISE.md").write_text(text, encoding="utf-8")
        return practice

    def renumber(self, practice, curriculums=CURRICULUMS):
        return run("renumber", "GIT", "--curriculums", curriculums, "--practice", practice)

    def retitled(self, titles):
        """A Curriculums directory holding a copy of GIT with each {filename: title} retitled in its H1."""
        curriculums = self.tmp / "curriculums"
        shutil.copytree(CURRICULUMS / "git", curriculums / "git")
        for name, title in titles.items():
            path = curriculums / "git" / name
            first, rest = path.read_text(encoding="utf-8").split("\n", 1)
            hashes, uid, _ = first.split(" ", 2)
            path.write_text(f"{hashes} {uid} {title}\n{rest}", encoding="utf-8")
        return curriculums

    def test_reports_an_exercise_whose_anchor_still_has_its_id_and_title_as_valid(self):
        practice = self.workspace({"GIT-01.01.02-01-list-refs": exercise_md("GIT-01.01.02", "Refs")})
        result = self.renumber(practice)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "GIT-01.01.02-01-list-refs: valid\n", ""))

    def test_reports_an_exercise_whose_title_now_heads_one_other_subsection_as_moved(self):
        # Refs was GIT-01.01.01 before a mid-Section insertion pushed it to GIT-01.01.02.
        practice = self.workspace({"GIT-01.01.01-01-list-refs": exercise_md("GIT-01.01.01", "Refs")})
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "GIT-01.01.01-01-list-refs: moved: GIT-01.01.01 → GIT-01.01.02\n", ""),
        )

    def test_reports_an_exercise_whose_title_heads_several_other_subsections_as_broken_with_them(self):
        curriculums = self.retitled({"GIT-03.01.01-cat-file.md": "Refs"})
        practice = self.workspace({"GIT-01.02.01-01-list-refs": exercise_md("GIT-01.02.01", "Refs")})
        result = self.renumber(practice, curriculums)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                0,
                'GIT-01.02.01-01-list-refs: broken: 2 Subsections are titled "Refs"\n'
                "  candidate: GIT-01.01.02 Refs\n"
                "  candidate: GIT-03.01.01 Refs\n",
                "",
            ),
        )

    def test_reports_an_exercise_whose_id_and_title_are_both_gone_as_broken_with_no_candidates(self):
        practice = self.workspace({"GIT-04.01.01-01-rebase-a-branch": exercise_md("GIT-04.01.01", "Rebasing")})
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, 'GIT-04.01.01-01-rebase-a-branch: broken: no Subsection is titled "Rebasing"\n', ""),
        )

    def test_reports_an_exercise_with_a_missing_or_unreadable_record_as_broken(self):
        cases = [
            ("no EXERCISE.md", None, "no EXERCISE.md"),
            ("no H1", exercise_md("GIT-01.01.02", "Refs").removeprefix("# Stage one file\n\n"), "EXERCISE.md has no anchor record"),
            ("no Anchor title", exercise_md("GIT-01.01.02", "Refs").replace("- Anchor title: Refs\n", ""), "EXERCISE.md has no anchor record"),
            ("a Section as anchor", exercise_md("GIT-01.01", "Objects"), "EXERCISE.md has no anchor record"),
            ("another Curriculum", exercise_md("GIT-01.01.02", "Refs", code="MATH"), "EXERCISE.md records Curriculum MATH"),
            ("not UTF-8", b"# Stage one file\n\n- Anchor title: R\xe9fs\n", "EXERCISE.md can't be read"),
        ]
        for case, text, reason in cases:
            with self.subTest(case):
                practice = self.tmp / case / "practice"
                (practice / "GIT" / "GIT-01.01.02-01-list-refs").mkdir(parents=True)
                md = practice / "GIT" / "GIT-01.01.02-01-list-refs" / "EXERCISE.md"
                if isinstance(text, bytes):
                    md.write_bytes(text)
                elif text is not None:
                    md.write_text(text, encoding="utf-8")
                result = self.renumber(practice)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr), (0, f"GIT-01.01.02-01-list-refs: broken: {reason}\n", "")
                )

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads a file whatever its mode")
    def test_reports_an_exercise_whose_record_cant_be_opened_as_broken(self):
        practice = self.workspace({"GIT-01.01.02-01-list-refs": exercise_md("GIT-01.01.02", "Refs")})
        (practice / "GIT" / "GIT-01.01.02-01-list-refs" / "EXERCISE.md").chmod(0)
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (0, "GIT-01.01.02-01-list-refs: broken: EXERCISE.md can't be read\n", "")
        )

    def test_reports_every_exercise_in_name_order_and_skips_other_directories(self):
        practice = self.workspace(
            {
                "GIT-01.01.02-02-list-tags": exercise_md("GIT-01.01.02", "Refs"),
                "GIT-01.01.01-01-list-refs": exercise_md("GIT-01.01.01", "Refs"),
            }
        )
        (practice / "GIT" / "notes.txt").write_text("not an Exercise\n", encoding="utf-8")
        (practice / "GIT" / ".generating").mkdir()
        (practice / "GIT" / "scratch").mkdir()
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "GIT-01.01.01-01-list-refs: moved: GIT-01.01.01 → GIT-01.01.02\nGIT-01.01.02-02-list-tags: valid\n", ""),
        )

    def test_reports_none_when_the_curriculum_has_no_exercises(self):
        (self.tmp / "empty" / "GIT").mkdir(parents=True)
        for empty in (self.tmp / "empty", self.tmp / "missing"):
            with self.subTest(empty.name):
                result = self.renumber(empty)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "None\n", ""))

    def test_writes_nothing(self):
        practice = self.workspace(
            {
                "GIT-01.01.01-01-list-refs": exercise_md("GIT-01.01.01", "Refs"),
                "GIT-04.01.01-01-rebase-a-branch": exercise_md("GIT-04.01.01", "Rebasing"),
            }
        )

        def snapshot():
            return sorted((str(p.relative_to(self.tmp)), p.is_file() and p.read_bytes(), p.stat().st_mtime_ns) for p in self.tmp.rglob("*"))

        before = snapshot()
        result = self.renumber(practice)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(snapshot(), before)

    def test_reports_an_exercise_whose_name_lags_its_record_as_moved(self):
        # A rename that rewrote the record but stopped before renaming the directory.
        practice = self.workspace({"GIT-01.01.01-01-list-refs": exercise_md("GIT-01.01.02", "Refs")})
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "GIT-01.01.01-01-list-refs: moved: GIT-01.01.01 → GIT-01.01.02\n", ""),
        )

    def test_reports_an_exercise_whose_record_lags_its_name_as_moved(self):
        practice = self.workspace({"GIT-01.01.02-01-list-refs": exercise_md("GIT-01.01.01", "Refs")})
        result = self.renumber(practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "GIT-01.01.02-01-list-refs: moved: GIT-01.01.01 → GIT-01.01.02\n", ""),
        )

    def test_stops_when_the_curriculum_cant_be_found(self):
        result = self.renumber(self.workspace({}), self.tmp)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (1, "", f"renumber: no Curriculum in {self.tmp.resolve()} has code GIT\n")
        )

    def test_reports_an_exercise_whose_anchor_was_retitled_as_broken_not_moved(self):
        curriculums = self.retitled({"GIT-01.01.02-refs.md": "References"})
        practice = self.workspace({"GIT-01.01.02-01-list-refs": exercise_md("GIT-01.01.02", "Refs")})
        result = self.renumber(practice, curriculums)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                0,
                'GIT-01.01.02-01-list-refs: broken: no Subsection is titled "Refs"\n'
                "  candidate: GIT-01.01.02 References\n",
                "",
            ),
        )


class Rename(TempDirTestCase):
    def workspace(self, *names):
        """A Practice workspace holding GIT/<name>/ for each name, recorded as anchored at the ID its name starts with, titled Refs."""
        practice = self.tmp / "practice"
        for name in names:
            anchor = name.split("-")[0] + "-" + name.split("-")[1]
            (practice / "GIT" / name / "hints").mkdir(parents=True)
            (practice / "GIT" / name / "EXERCISE.md").write_text(exercise_md(anchor, "Refs"), encoding="utf-8")
            (practice / "GIT" / name / "hints" / "1.md").write_text("Which ref moves?\n", encoding="utf-8")
        return practice

    def rename(self, exercise, new_id, curriculums=CURRICULUMS):
        return run("rename", exercise, new_id, "--curriculums", curriculums)

    def tree(self):
        return sorted((str(p.relative_to(self.tmp)), p.is_file() and p.read_text(encoding="utf-8")) for p in self.tmp.rglob("*"))

    def test_rewrites_the_record_then_renames_the_directory_under_the_new_id(self):
        practice = self.workspace("GIT-01.01.01-01-list-refs")
        result = self.rename(practice / "GIT" / "GIT-01.01.01-01-list-refs", "GIT-01.01.02")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "renamed: GIT-01.01.01-01-list-refs → GIT-01.01.02-01-list-refs\n", ""),
        )
        self.assertEqual(
            self.tree(),
            [
                ("practice", False),
                ("practice/GIT", False),
                ("practice/GIT/GIT-01.01.02-01-list-refs", False),
                ("practice/GIT/GIT-01.01.02-01-list-refs/EXERCISE.md", exercise_md("GIT-01.01.02", "Refs")),
                ("practice/GIT/GIT-01.01.02-01-list-refs/hints", False),
                ("practice/GIT/GIT-01.01.02-01-list-refs/hints/1.md", "Which ref moves?\n"),
            ],
        )

    def test_takes_the_next_free_number_under_the_new_id_and_keeps_the_slug(self):
        practice = self.workspace("GIT-01.01.01-02-list-refs", "GIT-01.01.02-01-show-head", "GIT-01.01.02-03-move-a-branch")
        result = self.rename(practice / "GIT" / "GIT-01.01.01-02-list-refs", "GIT-01.01.02")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "renamed: GIT-01.01.01-02-list-refs → GIT-01.01.02-04-list-refs\n", ""),
        )
        self.assertEqual(
            sorted(d.name for d in (practice / "GIT").iterdir()),
            ["GIT-01.01.02-01-show-head", "GIT-01.01.02-03-move-a-branch", "GIT-01.01.02-04-list-refs"],
        )

    def test_records_the_new_anchors_title_and_keeps_the_rest_of_exercise_md(self):
        practice = self.workspace("GIT-01.01.01-01-list-refs")
        exercise = practice / "GIT" / "GIT-01.01.01-01-list-refs"
        result = self.rename(exercise, "GIT-01.02.01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (practice / "GIT" / "GIT-01.02.01-01-list-refs" / "EXERCISE.md").read_text(encoding="utf-8"),
            exercise_md("GIT-01.02.01", "The index as a staging snapshot"),
        )

    def test_keeps_each_lines_ending(self):
        practice = self.workspace("GIT-01.01.01-01-list-refs")
        md = practice / "GIT" / "GIT-01.01.01-01-list-refs" / "EXERCISE.md"
        md.write_bytes(exercise_md("GIT-01.01.01", "Refs").replace("\n", "\r\n").encode("utf-8"))
        result = self.rename(md.parent, "GIT-01.01.02")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (practice / "GIT" / "GIT-01.01.02-01-list-refs" / "EXERCISE.md").read_bytes(),
            exercise_md("GIT-01.01.02", "Refs").replace("\n", "\r\n").encode("utf-8"),
        )

    def test_keeps_the_directory_when_the_id_is_unchanged(self):
        # Settling a retitled anchor: the ID stays and only the recorded title changes.
        practice = self.workspace("GIT-01.02.01-01-list-refs")
        result = self.rename(practice / "GIT" / "GIT-01.02.01-01-list-refs", "GIT-01.02.01")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "renamed: GIT-01.02.01-01-list-refs → GIT-01.02.01-01-list-refs\n", ""),
        )
        self.assertEqual(
            (practice / "GIT" / "GIT-01.02.01-01-list-refs" / "EXERCISE.md").read_text(encoding="utf-8"),
            exercise_md("GIT-01.02.01", "The index as a staging snapshot"),
        )

    def test_stops_and_changes_nothing_when_it_cant_rename(self):
        practice = self.workspace("GIT-01.01.01-01-list-refs", "not-an-exercise", "GIT-00.01.01-01-level-zero")
        (practice / "GIT" / "GIT-01.01.01-02-no-record").mkdir()
        cases = [
            ("GIT-01.01.01-01-list-refs", "GIT-01.01", "rename: GIT-01.01 isn't a Subsection ID\n"),
            ("GIT-01.01.01-01-list-refs", "GIT-01.01.09", "rename: GIT-01.01.09 names no Subsection in git\n"),
            ("GIT-01.01.01-01-list-refs", "MATH-01.01.01", "rename: MATH-01.01.01 isn't in Curriculum GIT\n"),
            ("not-an-exercise", "GIT-01.01.02", "rename: not-an-exercise isn't named <ID>-<NN>-<slug>\n"),
            ("GIT-00.01.01-01-level-zero", "GIT-01.01.02", "rename: GIT-00.01.01-01-level-zero isn't named <ID>-<NN>-<slug>\n"),
            ("GIT-01.01.01-02-no-record", "GIT-01.01.02", "rename: GIT-01.01.01-02-no-record: no EXERCISE.md\n"),
            ("GIT-01.01.01-09-missing", "GIT-01.01.02", "rename: GIT-01.01.01-09-missing isn't a directory\n"),
        ]
        before = self.tree()
        for name, new_id, message in cases:
            with self.subTest(name=name, new_id=new_id):
                result = self.rename(practice / "GIT" / name, new_id)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))
                self.assertEqual(self.tree(), before)


class FormatVersion(TempDirTestCase):
    def test_refuses_to_run_when_build_py_reads_another_format_version(self):
        skills = self.tmp / "skills"
        build = skills / "build-curriculum" / "scripts" / "build.py"
        script = skills / "build-exercises" / "scripts" / "exercises.py"
        for src, dst in ((REPO / "skills" / "build-curriculum" / "scripts" / "build.py", build), (SCRIPT, script)):
            dst.parent.mkdir(parents=True)
            shutil.copy(src, dst)
        text = build.read_text(encoding="utf-8")
        self.assertEqual(text.count("\nFORMAT_VERSION = 2\n"), 1)
        build.write_text(text.replace("\nFORMAT_VERSION = 2\n", "\nFORMAT_VERSION = 3\n"), encoding="utf-8")
        result = run("context", "GIT-01.02.01", "--curriculums", CURRICULUMS, script=script)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                1,
                "",
                "exercises: Format version 2 differs from build-curriculum's build.py, "
                "which reads Format version 3; update both skills together\n",
            ),
        )


if __name__ == "__main__":
    unittest.main()
