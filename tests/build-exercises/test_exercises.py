"""Tests for skills/build-exercises/scripts/exercises.py, driven only through its CLI."""

import json
import os
import shlex
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
