"""Tests for skills/build-exercises/scripts/exercises.py, driven only through its CLI, and for the Domain references it reads."""

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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
        self.assertTrue(domain_md_errors(swapped)[0].startswith("has headings "), domain_md_errors(swapped))

    def test_the_heading_check_catches_a_missing_applies_to_line(self):
        text = (DOMAINS / "toy" / "domain.md").read_text(encoding="utf-8")
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

    def test_keeps_a_templates_line_endings_and_mirrors_empty_directories(self):
        shutil.copytree(DOMAINS / "toy", self.tmp / "domains" / "toy")
        assets = self.tmp / "domains" / "toy" / "assets"
        (assets / "run.bat.tmpl").write_bytes(b"echo {{exercise_name}}\r\nexit\r\n")
        (assets / "levels").mkdir()
        self.assertEqual(self.assets("GIT-01.02.01-03-stage-a-file", domains=self.tmp / "domains").returncode, 0)
        self.assertEqual((self.tmp / "gen" / "run.bat").read_bytes(), b"echo GIT-01.02.01-03-stage-a-file\r\nexit\r\n")
        self.assertTrue((self.tmp / "gen" / "levels").is_dir())

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
            ("rust", "GIT-01.02.01-03-stage-a-file", f"assets: no Domain reference rust in {DOMAINS}; found: toy\n"),
            ("toy", "GIT-01.02.01-03-stage-a-file", f"assets: {self.tmp / 'gen'} isn't an empty directory; assets fills a fresh Generation directory\n"),
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
            (1, "", "assets: toy: assets/check.sh.tmpl is missing; every Domain reference needs it\n"),
        )


COVERED_EXERCISE_MD = """# Stage one file

- Curriculum: GIT
- Anchor: GIT-01.02.01
- Anchor title: The index as a staging snapshot

## Task

Stage `a.txt` and nothing else.

## Done when

- `a.txt` is staged.
- `b.txt` stays unstaged.
- Run `git status`: only `a.txt` is green. **(check by eye)**

## Given

The repository with `a.txt` and `b.txt`.

```text
## not a heading
```

`lib/helpers.sh`, except `helper`.

## Check

Run `./check.sh` from this folder.
"""


def listed(result):
    """existing's exit code, its lines naming an Exercise or the next <NN>, and its stderr, leaving out what each Exercise covered."""
    names = "".join(line for line in result.stdout.splitlines(keepends=True) if not line.startswith(" ") and line.strip())
    return result.returncode, names, result.stderr


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
        self.assertEqual(listed(result), (0, "None\nNext: 01\n", ""))

    def test_next_follows_the_highest_number_and_never_fills_a_gap(self):
        practice = self.workspace("GIT/GIT-01.02.01-03-amend-a-snapshot", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(
            listed(result),
            (0, "GIT-01.02.01-01-stage-one-file\nGIT-01.02.01-03-amend-a-snapshot\nNext: 04\n", ""),
        )

    def test_counts_an_exercise_with_an_empty_slug(self):
        practice = self.workspace("GIT/GIT-01.02.01-01-")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(listed(result), (0, "GIT-01.02.01-01-\nNext: 02\n", ""))

    def test_skips_another_subsections_exercises(self):
        practice = self.workspace("GIT/GIT-01.01.01-04-hash-a-blob", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(listed(result), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", ""))

    def test_skips_exercises_in_another_curriculums_directory(self):
        practice = self.workspace("MATH/GIT-01.02.01-05-misfiled", "GIT/GIT-01.02.01-01-stage-one-file")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(listed(result), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", ""))

    def test_reads_practice_in_the_curriculums_directory_by_default(self):
        self.workspace("GIT/GIT-01.02.01-01-stage-one-file")
        for args, cwd in [(["--curriculums", self.tmp], None), ([], self.tmp)]:
            with self.subTest(args=args):
                result = run("existing", "GIT-01.02.01", *args, cwd=cwd)
                self.assertEqual(
                    listed(result), (0, "GIT-01.02.01-01-stage-one-file\nNext: 02\n", "")
                )

    def test_shows_what_each_exercise_covered_from_its_exercise_md_and_its_markers(self):
        practice = self.workspace("GIT/GIT-01.02.01-01-stage-one-file")
        exercise = practice / "GIT" / "GIT-01.02.01-01-stage-one-file"
        (exercise / "EXERCISE.md").write_text(COVERED_EXERCISE_MD, encoding="utf-8")
        (exercise / "stage.sh").write_text("#!/bin/sh\nset -e\n# Your code goes here.\n", encoding="utf-8")
        (exercise / "lib").mkdir()
        (exercise / "lib" / "helpers.sh").write_text("helper() {\n  # Your code goes here.\n}\n", encoding="utf-8")
        (exercise / "repo.cfg").write_text("no marker here\n", encoding="utf-8")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                0,
                "GIT-01.02.01-01-stage-one-file\n"
                "  Title: Stage one file\n"
                "  Done when:\n"
                "    - `a.txt` is staged.\n"
                "    - `b.txt` stays unstaged.\n"
                "    - Run `git status`: only `a.txt` is green. **(check by eye)**\n"
                "  Given:\n"
                "    The repository with `a.txt` and `b.txt`.\n"
                "\n"
                "    ```text\n"
                "    ## not a heading\n"
                "    ```\n"
                "\n"
                "    `lib/helpers.sh`, except `helper`.\n"
                "  Markers:\n"
                "    lib/helpers.sh:2\n"
                "    stage.sh:3\n"
                "Next: 02\n",
                "",
            ),
        )

    def test_finds_markers_only_in_the_starter_and_says_when_none_are_left(self):
        practice = self.workspace("GIT/GIT-01.02.01-01-stage-one-file")
        exercise = practice / "GIT" / "GIT-01.02.01-01-stage-one-file"
        (exercise / "EXERCISE.md").write_text(COVERED_EXERCISE_MD, encoding="utf-8")
        (exercise / "check.sh").write_text("# Your code goes here.\n", encoding="utf-8")
        for rel in ["check/lines.sh", "hints/2.md"]:
            (exercise / rel).parent.mkdir()
            (exercise / rel).write_text("Your code goes here.\n", encoding="utf-8")
        (exercise / "stage.sh").write_text("git add a.txt\n", encoding="utf-8")  # the learner replaced the marker
        (exercise / ".godot").mkdir()  # the tool's cache, which may copy a starter file
        (exercise / ".godot" / "stage.sh").write_text("# Your code goes here.\n", encoding="utf-8")
        (exercise / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertIn("\n  Markers: none\nNext: 02\n", result.stdout)

    def test_says_what_it_cant_read_from_an_exercise(self):
        practice = self.workspace("GIT/GIT-01.02.01-01-no-sections", "GIT/GIT-01.02.01-02-no-exercise-md")
        (practice / "GIT" / "GIT-01.02.01-02-no-exercise-md" / "EXERCISE.md").unlink()
        result = run("existing", "GIT-01.02.01", "--practice", practice)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                0,
                "GIT-01.02.01-01-no-sections\n"
                "  Title: An Exercise\n"
                "  Done when: none\n"
                "  Given: none\n"
                "  Markers: none\n"
                "GIT-01.02.01-02-no-exercise-md\n"
                "  no EXERCISE.md\n"
                "Next: 03\n",
                "",
            ),
        )

    def test_stops_on_an_id_that_isnt_a_subsection(self):
        for token, message in [
            ("GIT-01.02", "existing: GIT-01.02 isn't a Subsection ID\n"),
            ("git", "existing: git isn't an ID\n"),
        ]:
            with self.subTest(token):
                result = run("existing", token, "--practice", self.tmp)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))


WALKS = "It walks to the well at 3 meters per second."
TICKS = "It moves only on physics ticks."
ERRORS = "No script errors."
BY_EYE = "Run `main.tscn`: its feet stay on the ramp."
GATE_JSON = {
    "lines": [
        {"text": WALKS, "kind": "outcome"},
        {"text": TICKS, "kind": "outcome"},
        {"text": ERRORS, "kind": "guard"},
        {"text": BY_EYE, "kind": "self-check"},
    ],
    "near_misses": {"too-slow": WALKS, "moves-in-process": TICKS},
}


def fake_check(*runs):
    """A check.sh printing each run's (exit code, lines[, stderr lines]) in turn, then repeating the last run.

    It counts its runs in a file beside itself, so a flake across reruns can be faked.
    """
    script = ["#!/bin/sh", 'n=$(cat runs 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > runs']
    for i, (code, lines, *stderr) in enumerate(runs, 1):
        test = "true" if i == len(runs) else f'[ "$n" -eq {i} ]'
        body = "".join(f"printf '%s\\n' {shlex.quote(line)}; " for line in lines)
        body += "".join(f"printf '%s\\n' {shlex.quote(line)} >&2; " for line in (stderr[0] if stderr else []))
        script.append(f"if {test}; then {body}exit {code}; fi")
    return "\n".join(script) + "\n"


def lines(walks, ticks, errors="PASS"):
    """A run's printed lines, given each automated line's status."""
    return [
        f"{walks} {WALKS} (3.02 m/s)",
        f"{ticks} {TICKS} (0 moves in _process)",
        f"{errors} {ERRORS} (0 errors)",
        "1 of 3 lines failed." if "FAIL" in (walks, ticks, errors) else "All 3 lines passed.",
        "CHECK YOURSELF",
        f"- {BY_EYE}",
    ]


PASSING = (0, lines("PASS", "PASS"))


def wait_for_pid(path, seconds=10):
    """The PID a process writes to path, once it has written it."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        if text:
            return int(text)
        time.sleep(0.05)
    raise AssertionError(f"nothing wrote a PID to {path} within {seconds} s")


def alive(pid, seconds=2):
    """Whether pid still runs after up to seconds, which gives a killed process time to be reaped."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        if time.monotonic() >= deadline:
            return True
        time.sleep(0.05)


class Gate(TempDirTestCase):
    def generation(self, starter, reference=PASSING, near_misses=None, gate_json=GATE_JSON):
        """A generation directory holding an Exercise and its gate files, each case's check.sh faking its runs.

        Each case swaps in its own check.sh, so a case's lines show the gate ran that case's files.
        """
        if near_misses is None:
            near_misses = {"too-slow": [(1, lines("FAIL", "PASS"))], "moves-in-process": [(1, lines("PASS", "FAIL"))]}
        gen = self.tmp / "gen"
        exercise = gen / "GIT-01.02.01-01-stage-one-file"
        cases = {exercise: starter, gen / "reference": [reference]}
        cases.update({gen / "near-misses" / name: runs for name, runs in near_misses.items()})
        for path, runs in cases.items():
            path.mkdir(parents=True)
            check = path / "check.sh"
            check.write_text(fake_check(*runs), encoding="utf-8")
            check.chmod(0o755)
        (exercise / "EXERCISE.md").write_text("# Stage one file\n", encoding="utf-8")
        (gen / "gate.json").write_text(json.dumps(gate_json), encoding="utf-8")
        return exercise, gen

    def test_passes_an_exercise_check_that_fails_the_starter_and_each_near_miss_and_passes_the_reference(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        result = run("gate", exercise, gen)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                0,
                "Cases: starter, reference, too-slow, moves-in-process\n"
                f"outcome  FFF PPP FFF PPP  {WALKS}\n"
                f"outcome  FFF PPP PPP FFF  {TICKS}\n"
                f"guard    PPP PPP PPP PPP  {ERRORS}\n"
                "\n"
                "Verdict: pass\n",
                "",
            ),
        )

    def test_fails_an_outcome_line_that_passes_on_the_starter(self):
        exercise, gen = self.generation([(1, lines("PASS", "FAIL"))])
        result = run("gate", exercise, gen)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                1,
                "Cases: starter, reference, too-slow, moves-in-process\n"
                f"outcome  PPP PPP FFF PPP  {WALKS}\n"
                f"outcome  FFF PPP PPP FFF  {TICKS}\n"
                f"guard    PPP PPP PPP PPP  {ERRORS}\n"
                "\n"
                f"Broken: passes on the starter: {WALKS}\n"
                "Verdict: fail\n",
                "",
            ),
        )

    def test_fails_a_near_miss_that_fails_another_line_than_the_one_it_targets(self):
        exercise, gen = self.generation(
            [(1, lines("FAIL", "FAIL"))],
            near_misses={"too-slow": [(1, lines("PASS", "FAIL"))], "moves-in-process": [(1, lines("PASS", "FAIL"))]},
        )
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                f"outcome  FFF PPP PPP PPP  {WALKS}\n"
                f"outcome  FFF PPP FFF FFF  {TICKS}\n"
                f"guard    PPP PPP PPP PPP  {ERRORS}\n"
                "\n"
                f"Broken: passes on the Near-miss too-slow: {WALKS}\n"
                "Verdict: fail\n"
            ),
            result.stdout,
        )

    def test_fails_a_line_that_flakes_across_reruns(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL")), (1, lines("FAIL", "PASS")), (1, lines("FAIL", "FAIL"))])
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                f"outcome  FFF PPP FFF PPP  {WALKS}\n"
                f"outcome  FPF PPP PPP FFF  {TICKS}\n"
                f"guard    PPP PPP PPP PPP  {ERRORS}\n"
                "\n"
                f"Broken: gives different results across reruns on the starter: {TICKS}\n"
                "Verdict: fail\n"
            ),
            result.stdout,
        )

    def test_holds_a_guard_line_only_to_passing_on_the_reference(self):
        exercise, gen = self.generation(
            [(1, lines("FAIL", "FAIL", "PASS"))],
            reference=(1, lines("PASS", "PASS", "FAIL")),
            near_misses={"too-slow": [(1, lines("FAIL", "PASS", "FAIL"))], "moves-in-process": [(1, lines("PASS", "FAIL"))]},
        )
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                f"guard    PPP FFF FFF PPP  {ERRORS}\n"
                "\n"
                f"Broken: fails on the reference: {ERRORS}\n"
                "Verdict: fail\n"
            ),
            result.stdout,
        )

    def test_reports_an_exit_2_as_an_environment_problem_not_a_line_failure(self):
        exercise, gen = self.generation(
            [(1, lines("FAIL", "FAIL"))],
            reference=(2, [], ["Starting the check.", "godot: command not found"]),
        )
        result = run("gate", exercise, gen)
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                2,
                "Cases: starter, reference, too-slow, moves-in-process\n"
                f"outcome  FFF EEE FFF PPP  {WALKS}\n"
                f"outcome  FFF EEE PPP FFF  {TICKS}\n"
                f"guard    PPP EEE PPP PPP  {ERRORS}\n"
                "\n"
                "Environment problem: the reference exits 2 on runs 1, 2, 3: godot: command not found\n"
                "Verdict: environment problem\n",
                "",
            ),
        )

    def test_reports_an_exit_2_on_one_rerun_and_judges_the_others(self):
        exercise, gen = self.generation([(1, lines("PASS", "FAIL")), (2, lines("FAIL", "FAIL")), (1, lines("PASS", "FAIL"))])
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                f"outcome  PEP PPP FFF PPP  {WALKS}\n"
                f"outcome  FEF PPP PPP FFF  {TICKS}\n"
                f"guard    PEP PPP PPP PPP  {ERRORS}\n"
                "\n"
                "Environment problem: the starter exits 2 on run 2\n"
                f"Broken: passes on the starter: {WALKS}\n"
                "Verdict: environment problem\n"
            ),
            result.stdout,
        )

    def test_reports_a_run_that_outlasts_the_timeout_as_an_environment_problem(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        check = exercise / "check.sh"
        # The sleep is a child of check.sh, as Godot is, so it holds the output open after check.sh itself is killed.
        script = check.read_text(encoding="utf-8").split("\n")
        starts = self.tmp / "starter-runs"  # outside the copy the gate runs, so it outlives the run
        script.insert(2, f'echo "$n" > {shlex.quote(str(starts))}; if [ "$n" -eq 2 ]; then sleep 60; fi')  # after the line counting the runs
        check.write_text("\n".join(script), encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "gate", "--timeout", "1", exercise, gen],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
        except subprocess.TimeoutExpired:
            self.fail("gate hung on a run that outlasted --timeout")
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (
                2,
                "Cases: starter, reference, too-slow, moves-in-process\n"
                f"outcome  FEE PPP FFF PPP  {WALKS}\n"
                f"outcome  FEE PPP PPP FFF  {TICKS}\n"
                f"guard    PEE PPP PPP PPP  {ERRORS}\n"
                "\n"
                "Environment problem: the starter didn't finish within 1 s on run 2, so the gate skipped run 3\n"
                "Verdict: environment problem\n",
                "",
            ),
        )
        self.assertEqual(starts.read_text(encoding="utf-8"), "2\n")

    def test_kills_the_running_exercise_check_when_the_gate_is_stopped(self):
        for sig in (signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signal=sig.name):
                shutil.rmtree(self.tmp / "gen", ignore_errors=True)
                exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
                pid_file = self.tmp / "sleep-pid"
                pid_file.unlink(missing_ok=True)
                # The sleep is a child of check.sh, as Godot is; it writes its PID outside the copy the gate runs.
                check = exercise / "check.sh"
                check.write_text(f"#!/bin/sh\nsleep 4242 &\necho $! > {shlex.quote(str(pid_file))}\nwait\n", encoding="utf-8")
                # A group of its own, as a shell tool gives the commands it runs, so the signal goes to the group.
                gate = subprocess.Popen(
                    [sys.executable, str(SCRIPT), "gate", exercise, gen],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
                )
                sleep_pid = None
                try:
                    sleep_pid = wait_for_pid(pid_file)
                    os.killpg(gate.pid, sig)
                    self.assertEqual(gate.wait(timeout=10), 128 + sig)
                    self.assertFalse(alive(sleep_pid), "the Exercise check's child outlived the gate")
                finally:
                    if gate.poll() is None:
                        gate.kill()
                        gate.wait()
                    if sleep_pid and alive(sleep_pid):
                        os.kill(sleep_pid, signal.SIGKILL)

    def test_leaves_the_exercise_directory_as_it_was(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        (exercise / "main.gd").write_text("# Your code goes here.\n", encoding="utf-8")
        (gen / "reference" / "main.gd").write_text("func _physics_process(delta):\n", encoding="utf-8")

        def snapshot():
            return {p.relative_to(exercise): p.read_bytes() for p in sorted(exercise.rglob("*")) if p.is_file()}

        before = snapshot()
        result = run("gate", exercise, gen)  # each fake check.sh writes its run count beside itself
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(), before)

    def test_stops_on_a_gate_json_that_breaks_the_exercise_format(self):
        guard_target = {**GATE_JSON, "near_misses": {**GATE_JSON["near_misses"], "too-slow": ERRORS}}
        untargeted = {**GATE_JSON, "near_misses": {"too-slow": WALKS}}
        unknown_kind = {**GATE_JSON, "lines": GATE_JSON["lines"] + [{"text": "It hums.", "kind": "sound"}]}
        repeated = {**GATE_JSON, "lines": GATE_JSON["lines"] + [{"text": WALKS, "kind": "guard"}]}
        for name, gate_json, near_misses, message in [
            ("a Near-miss targets a guard line", guard_target, None, f"the Near-miss too-slow targets {ERRORS!r}, which isn't an outcome line"),
            ("a Near-miss targets no line", {**GATE_JSON, "near_misses": {**GATE_JSON["near_misses"], "too-slow": "It flies."}}, None, "the Near-miss too-slow targets 'It flies.', which isn't an outcome line"),
            ("an outcome line no Near-miss targets", untargeted, {"too-slow": [(1, lines("FAIL", "PASS"))]}, f"no Near-miss targets the outcome line {TICKS!r}"),
            ("a Near-miss named after another case", {**GATE_JSON, "near_misses": {"reference": WALKS, "moves-in-process": TICKS}}, {"reference": [(1, lines("FAIL", "PASS"))], "moves-in-process": [(1, lines("PASS", "FAIL"))]}, "a Near-miss can't be named reference, which names another case"),
            ("an unknown kind", unknown_kind, None, "the line 'It hums.' has kind 'sound', not outcome, guard or self-check"),
            ("a repeated text", repeated, None, f"two lines have the text {WALKS!r}"),
            ("a directory with no entry", untargeted, None, "near-misses/moves-in-process has no entry in gate.json"),
            ("an entry with no directory", GATE_JSON, {"too-slow": [(1, lines("FAIL", "PASS"))]}, "the Near-miss moves-in-process has no directory under near-misses/"),
        ]:
            with self.subTest(name):
                self.tmp = Path(self._tmp.name) / name.replace(" ", "-")  # a generation directory of its own
                exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))], near_misses=near_misses, gate_json=gate_json)
                result = run("gate", exercise, gen)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", f"gate: {message}\n"))

    def test_stops_on_a_missing_or_unreadable_gate_json(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        (gen / "gate.json").write_text("{", encoding="utf-8")
        result = run("gate", exercise, gen)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertTrue(result.stderr.startswith("gate: gate.json isn't valid JSON: "), result.stderr)
        (gen / "gate.json").unlink()
        result = run("gate", exercise, gen)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertTrue(result.stderr.startswith("gate: "), result.stderr)

    def test_fails_an_automated_line_gate_json_doesnt_name(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL") + ["PASS It hums. (440 Hz)"])])
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith("\nBroken: printed on the starter but not in gate.json: It hums.\nVerdict: fail\n"), result.stdout
        )

    def test_tells_apart_a_line_whose_text_starts_with_another_lines_text(self):
        longer = f"{WALKS} (on flat ground) and up the ramp."
        gate_json = {
            "lines": GATE_JSON["lines"] + [{"text": longer, "kind": "outcome"}],
            "near_misses": {**GATE_JSON["near_misses"], "stops-at-ramp": longer},
        }
        printed = lambda walks, ramp, ticks="PASS": lines(walks, ticks)[:1] + [f"{ramp} {longer} (2.00 m)"] + lines(walks, ticks)[1:]
        exercise, gen = self.generation(
            [(1, printed("FAIL", "FAIL", "FAIL"))],
            reference=(0, printed("PASS", "PASS")),
            near_misses={
                "too-slow": [(1, printed("FAIL", "PASS"))],
                "moves-in-process": [(1, printed("PASS", "PASS", "FAIL"))],
                "stops-at-ramp": [(1, printed("PASS", "FAIL"))],
            },
            gate_json=gate_json,
        )
        result = run("gate", exercise, gen)
        self.assertEqual((result.returncode, result.stdout.splitlines()[-1]), (0, "Verdict: pass"), result.stdout)


    def test_fails_a_case_whose_exit_code_disagrees_with_its_lines(self):
        exercise, gen = self.generation(
            [(0, lines("FAIL", "FAIL"))],
            reference=(1, lines("PASS", "PASS")),
        )
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                "\n"
                "Broken: the starter exits 0 on runs 1, 2, 3 though a line failed\n"
                "Broken: the reference exits 1 on runs 1, 2, 3 though every line passed\n"
                "Verdict: fail\n"
            ),
            result.stdout,
        )

    def test_reports_a_declared_line_printed_without_its_measured_value(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))], reference=(0, lines("PASS", "PASS")[:2] + [f"PASS {ERRORS}"]))
        result = run("gate", exercise, gen)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(
            result.stdout.endswith(
                f"guard    PPP PPP PPP PPP  {ERRORS}\n"
                "\n"
                f"Broken: printed without a measured value in parentheses on the reference: {ERRORS}\n"
                "Verdict: fail\n"
            ),
            result.stdout,
        )

    def test_runs_an_exercise_named_by_a_relative_path(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        for path in (".", "sub/.."):
            with self.subTest(path):
                (exercise / "sub").mkdir(exist_ok=True)
                result = run("gate", path, gen.resolve(), cwd=exercise)
                self.assertEqual((result.returncode, result.stdout.endswith("Verdict: pass\n")), (0, True), result.stdout + result.stderr)

    def test_stops_on_a_generation_directory_with_no_reference(self):
        exercise, gen = self.generation([(1, lines("FAIL", "FAIL"))])
        shutil.rmtree(gen / "reference")
        result = run("gate", exercise, gen)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", "gate: the Reference solution has no directory reference/\n"))


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

    def test_keeps_lone_cr_endings(self):
        practice = self.workspace("GIT-01.01.01-01-list-refs")
        md = practice / "GIT" / "GIT-01.01.01-01-list-refs" / "EXERCISE.md"
        md.write_bytes(exercise_md("GIT-01.01.01", "Refs").replace("\n", "\r").encode("utf-8"))
        result = self.rename(md.parent, "GIT-01.01.02")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (practice / "GIT" / "GIT-01.01.02-01-list-refs" / "EXERCISE.md").read_bytes(),
            exercise_md("GIT-01.01.02", "Refs").replace("\n", "\r").encode("utf-8"),
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
