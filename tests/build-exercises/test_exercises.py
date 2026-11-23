"""Tests for skills/build-exercises/scripts/exercises.py, driven only through its CLI."""

import os
import re
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
DOMAINS = FIXTURES / "domains"  # toy, a stand-in domain reference
SKILL_DOMAINS = REPO / "skills" / "build-exercises" / "references" / "domains"

# domain.md's fixed H2 and H3 headings, in order, from docs/domain-reference.md.
DOMAIN_HEADINGS = [
    "## Environment",
    "### Tool",
    "### Self-contained",
    "### Project layout",
    "### Building the starter",
    "## Checking",
    "### Harness",
    "### Check lines",
    "### Stand-ins",
]


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


def domain_md_errors(text):
    """What breaks domain.md's fixed headings: an H1, an Applies-to line next, then DOMAIN_HEADINGS in order."""
    lines, fenced, headings = text.split("\n"), False, []
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,3} ", line):
            headings.append(line.rstrip())
    errors = []
    if not headings or not headings[0].startswith("# ") or lines[0] != headings[0]:
        errors.append("doesn't open with an H1 naming the domain")
    after_h1 = [line for line in lines[1:] if line.strip()]
    if not after_h1 or not after_h1[0].startswith("Applies to: "):
        errors.append("the line after the H1 isn't an Applies to: line")
    if headings[1:] != DOMAIN_HEADINGS:
        errors.append(f"has headings {headings[1:]}, not {DOMAIN_HEADINGS}")
    return errors


class DomainReferences(unittest.TestCase):
    def test_every_domain_md_has_the_fixed_headings_in_order(self):
        found = sorted(SKILL_DOMAINS.glob("*/domain.md")) + sorted(DOMAINS.glob("*/domain.md"))
        self.assertIn(DOMAINS / "toy" / "domain.md", found)
        for path in found:
            with self.subTest(str(path.relative_to(REPO))):
                self.assertEqual(domain_md_errors(path.read_text(encoding="utf-8")), [])
                self.assertTrue((path.parent / "assets" / "check.sh.tmpl").is_file(), "assets/check.sh.tmpl is missing")

    def test_the_heading_check_catches_a_heading_out_of_order(self):
        text = (DOMAINS / "toy" / "domain.md").read_text(encoding="utf-8")
        swapped = text.replace("### Harness", "### HOLD").replace("### Check lines", "### Harness").replace("### HOLD", "### Check lines")
        self.assertEqual(len(domain_md_errors(swapped)), 1)
        self.assertEqual(domain_md_errors(text.replace("Applies to: ", "For: ")), ["the line after the H1 isn't an Applies to: line"])


class Assets(TempDirTestCase):
    def assets(self, name, domains=DOMAINS, domain="toy"):
        return run("assets", domain, self.tmp / "gen", "--exercise-name", name, "--curriculums", CURRICULUMS, "--domains", domains)

    def test_fills_each_template_and_drops_its_suffix(self):
        result = self.assets("GIT-01.02.01-03-stage-a-file")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        gen = self.tmp / "gen"
        self.assertEqual(
            (gen / "check.sh").read_text(encoding="utf-8"),
            "#!/bin/sh\n"
            "# Runs the Exercise check for GIT-01.02.01-03-stage-a-file.\n"
            'target="2.47.1"\n'
            'exec toy --check "$(dirname "$0")" --target "$target"\n',
        )
        self.assertEqual((gen / "project.cfg").read_text(encoding="utf-8"), 'name = "GIT-01.02.01-03-stage-a-file"\n')
        self.assertFalse((gen / "check.sh.tmpl").exists())
        self.assertFalse((gen / "project.cfg.tmpl").exists())

    def test_copies_every_other_file_byte_for_byte_and_lists_what_it_wrote(self):
        result = self.assets("GIT-01.02.01-03-stage-a-file")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (0, "check.sh\ncheck/.gdignore\ncheck/harness.txt\nicon.png\nproject.cfg\n", ""),
        )
        gen, source = self.tmp / "gen", DOMAINS / "toy" / "assets"
        for rel in ("icon.png", "check/harness.txt", "check/.gdignore"):
            with self.subTest(rel):
                self.assertEqual((gen / rel).read_bytes(), (source / rel).read_bytes())
        self.assertIn(b"\xff{{exercise_name}}\xfe", (gen / "icon.png").read_bytes())  # left unfilled: not a template

    def test_keeps_a_templates_mode_so_check_sh_stays_executable(self):
        self.assertEqual(self.assets("GIT-01.02.01-03-stage-a-file").returncode, 0)
        self.assertTrue(os.access(self.tmp / "gen" / "check.sh", os.X_OK))

    def test_fills_target_version_empty_when_the_curriculum_has_none(self):
        result = self.assets("MATH-01.01.01-01-list-pairs")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertIn('target=""\n', (self.tmp / "gen" / "check.sh").read_text(encoding="utf-8"))

    def test_stops_on_an_unknown_placeholder_and_writes_nothing(self):
        shutil.copytree(DOMAINS / "toy", self.tmp / "domains" / "toy")
        (self.tmp / "domains" / "toy" / "assets" / "check" / "run.cfg.tmpl").write_text("a\nversion = {{target}}\n", encoding="utf-8")
        result = self.assets("GIT-01.02.01-03-stage-a-file", domains=self.tmp / "domains")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (1, "", "assets: check/run.cfg.tmpl:2: unknown placeholder {{target}}; only {{target_version}} and {{exercise_name}} are filled\n"),
        )
        self.assertFalse((self.tmp / "gen").exists())

    def test_stops_without_writing_when_it_cant_fill(self):
        (self.tmp / "gen").mkdir()
        (self.tmp / "gen" / "reference").mkdir()
        cases = [
            ("toy", "GIT-01.02.01-stage-a-file", "assets: GIT-01.02.01-stage-a-file isn't an Exercise name, <ID>-<NN>-<slug>\n"),
            ("toy", "GIT-01.02.09-01-stage-a-file", "assets: GIT-01.02.09 names no Subsection in git\n"),
            ("rust", "GIT-01.02.01-03-stage-a-file", f"assets: no domain reference rust in {DOMAINS}; found: toy\n"),
            ("toy", "GIT-01.02.01-03-stage-a-file", f"assets: {self.tmp / 'gen'} isn't an empty directory; assets fills a fresh generation directory\n"),
        ]
        for domain, name, message in cases:
            with self.subTest(message):
                result = self.assets(name, domain=domain)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))
                self.assertEqual([p.name for p in (self.tmp / "gen").iterdir()], ["reference"])

    def test_stops_when_the_domain_has_no_check_sh_template(self):
        shutil.copytree(DOMAINS / "toy", self.tmp / "domains" / "toy")
        (self.tmp / "domains" / "toy" / "assets" / "check.sh.tmpl").unlink()
        result = self.assets("GIT-01.02.01-03-stage-a-file", domains=self.tmp / "domains")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (1, "", "assets: toy: assets/check.sh.tmpl is missing; every domain reference needs it\n"),
        )


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
