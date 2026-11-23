#!/usr/bin/env python3
"""Do the deterministic jobs of build-exercises.

Subcommands:
  context <ID> [--curriculums <dir>]  print the Subsection and its Prereq closure
  existing <ID> [--curriculums <dir>] [--practice <dir>]
                                      list the Subsection's Exercises and the next <NN>
  gate <exercise-dir> <gen-dir>       run the Exercise check on every case and judge its lines

Reads doc sets through build-curriculum's build.py, so both skills parse a
Curriculum one way. FORMAT_VERSION is kept in step with ../references/curriculum-format.md,
and the script refuses to run when build.py's differs. Standard library only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# The plugin ships both skills, so the sibling's script is always beside this one.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build-curriculum" / "scripts"))
import build  # noqa: E402
from build import BuildError  # noqa: E402

FORMAT_VERSION = 2

# The Prereq closure shows each unit's Goal and Scope: what the learner holds, and how far it reaches.
CLOSURE_FIELDS = ["Goal", "Scope"]
# Fields printed with their links kept, because their links lead out of the doc set.
LINKS_KEPT = {"Sources"}


# --- Finding Curriculums -----------------------------------------------------


def curriculum_dir(directory, code):
    """The one Curriculum in directory with this code, or a string saying why there isn't one."""
    matches = build.curricula_with_code(directory, code)
    searched = Path(directory).resolve()  # named in full, because running from inside a Curriculum is the likely mistake
    if not matches:
        return f"no Curriculum in {searched} has code {code}"
    if len(matches) > 1:
        names = ", ".join(d.name for d in matches)
        return f"several Curriculums in {searched} have code {code}: {names}"
    return matches[0]


def subsections_by_code(directory):
    """A function from a code to that Curriculum's {UnitId: Unit}, or a string saying why it can't be read."""
    found = {}

    def find(code):
        if code not in found:
            found[code] = curriculum_dir(directory, code)
            if isinstance(found[code], Path):
                try:
                    found[code] = build.doc_set_subsections(found[code])
                except (BuildError, OSError):
                    found[code] = f"{code} doesn't load; run build.py check on {found[code].name}"
        return found[code]

    return find


def subsection_id(token):
    """The UnitId token names. Raises BuildError when it isn't a Subsection ID."""
    uid = build.parse_id(token)
    if not uid:
        raise BuildError(f"{token} isn't an ID")
    if len(uid.levels) != 3:
        raise BuildError(f"{token} isn't a Subsection ID")
    return uid


def anchor_units(directory, token):
    """(UnitId, {UnitId: Unit}) for the anchor's Curriculum. Raises BuildError when the anchor can't be read."""
    uid = subsection_id(token)
    root = curriculum_dir(directory, uid.code)
    if isinstance(root, str):
        raise BuildError(root)
    units = build.doc_set_subsections(root)  # its errors are printed in full: this run can't go on without them fixed
    if uid not in units:
        raise BuildError(f"{token} names no Subsection in {root.name}")
    return uid, units


# --- context -----------------------------------------------------------------


def closure(anchor, units, find):
    """{UnitId: Unit, or a string saying why it's unresolved} for every unit the anchor's Prereqs reach."""
    out = {}
    todo = build.direct_prereqs(units[anchor])
    while todo:
        uid = todo.pop(0)
        if uid in out or uid == anchor:
            continue
        found = units if uid.code == anchor.code else find(uid.code)
        if isinstance(found, str):
            out[uid] = found
        elif uid not in found:
            out[uid] = f"names no Subsection in {uid.code}"
        else:
            out[uid] = found[uid]
            todo.extend(build.direct_prereqs(found[uid]))
    return out


def context(directory, token):
    """The anchor's Fields, then its Prereq closure, own code first, each in ID order."""
    anchor, units = anchor_units(directory, token)
    unit = units[anchor]
    out = [f"# {anchor} {unit.title}\n"]
    for name, body in unit.fields.items():
        if body:
            out.append(f"## {name}\n\n{body if name in LINKS_KEPT else build.strip_links(body)}\n")
    out.append("# Prereq closure\n")
    reached = closure(anchor, units, subsections_by_code(directory))
    for uid in sorted(reached, key=lambda u: (u.code != anchor.code, u.code, u.levels)):
        found = reached[uid]
        if isinstance(found, str):
            out.append(f"## {uid}\n\nUnresolved: {found}\n")
            continue
        out.append(f"## {uid} {found.title}\n")
        for name in CLOSURE_FIELDS:
            if found.fields.get(name):
                out.append(f"### {name}\n\n{build.strip_links(found.fields[name])}\n")
    if not reached:
        out.append("None\n")
    return "\n".join(out)


# --- existing ----------------------------------------------------------------


def existing(practice, token):
    """The anchor's Exercises, lowest <NN> first, then the next <NN>."""
    uid = subsection_id(token)
    # Any slug, even an empty one, so a misnamed Exercise still holds its number.
    exercise = re.compile(rf"{re.escape(str(uid))}-([0-9]{{2,}})-.*")
    code_dir = Path(practice) / uid.code
    numbers = {}
    if code_dir.is_dir():
        for d in code_dir.iterdir():
            m = exercise.fullmatch(d.name)
            if m and d.is_dir():
                numbers[d.name] = int(m[1])
    # The highest plus one, never a gap's number, so a deleted Exercise's number isn't reused.
    next_nn = max(numbers.values(), default=0) + 1
    return "\n".join(sorted(numbers, key=numbers.get) or ["None"]) + f"\nNext: {next_nn:02d}\n"


# --- gate --------------------------------------------------------------------

# Each case runs this often, so a line that flakes across reruns shows before it ships.
RERUNS = 3
STATUS = {"PASS": "P", "FAIL": "F"}
KINDS = ("outcome", "guard", "self-check")


def read_manifest(gen):
    """gate.json, checked against exercise-format.md before any case runs. Raises BuildError when it breaks a rule."""
    try:
        manifest = json.loads((gen / "gate.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BuildError(f"gate.json isn't valid JSON: {e}") from None
    ok = isinstance(manifest, dict) and isinstance(manifest.get("lines"), list) and isinstance(manifest.get("near_misses"), dict)
    if not ok or not all(isinstance(line, dict) and isinstance(line.get("text"), str) for line in manifest["lines"]):
        raise BuildError("gate.json needs a lines list, each line with a text, and a near_misses object")
    seen = set()
    for line in manifest["lines"]:
        if line.get("kind") not in KINDS:
            raise BuildError(f"the line {line['text']!r} has kind {line.get('kind')!r}, not outcome, guard or self-check")
        if line["text"] in seen:
            raise BuildError(f"two lines have the text {line['text']!r}")
        seen.add(line["text"])
    outcomes = [line["text"] for line in manifest["lines"] if line["kind"] == "outcome"]
    for name, target in manifest["near_misses"].items():
        if name in ("starter", "reference"):
            raise BuildError(f"a Near-miss can't be named {name}, which names another case")
        if target not in outcomes:
            raise BuildError(f"the Near-miss {name} targets {target!r}, which isn't an outcome line")
    folder = gen / "near-misses"
    dirs = {d.name for d in folder.iterdir() if d.is_dir()} if folder.is_dir() else set()
    if unlisted := sorted(dirs - manifest["near_misses"].keys()):
        raise BuildError(f"near-misses/{unlisted[0]} has no entry in gate.json")
    if missing := sorted(manifest["near_misses"].keys() - dirs):
        raise BuildError(f"the Near-miss {missing[0]} has no directory under near-misses/")
    if untargeted := [text for text in outcomes if text not in manifest["near_misses"].values()]:
        raise BuildError(f"no Near-miss targets the outcome line {untargeted[0]!r}")
    if not (gen / "reference").is_dir():
        raise BuildError("the Reference solution has no directory reference/")
    return manifest


def gate_cases(gen):
    """gate.json and [(case name, directory of the files it swaps in, or None for the starter)]."""
    manifest = read_manifest(gen)
    cases = [("starter", None), ("reference", gen / "reference")]
    cases += [(name, gen / "near-misses" / name) for name in manifest["near_misses"]]
    return manifest, cases


def run_case(exercise, swap):
    """Each rerun's (exit code, stdout, stderr), from a copy of the Exercise with swap's files laid over it.

    The copy keeps the Exercise directory untouched, whatever the Exercise check or the swap writes.
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / exercise.resolve().name  # resolved, since "." or ".." has no name of its own
        shutil.copytree(exercise, work, symlinks=True)
        if swap:
            shutil.copytree(swap, work, symlinks=True, dirs_exist_ok=True)
        runs = []
        for _ in range(RERUNS):
            done = subprocess.run([str(work / "check.sh")], cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
            runs.append((done.returncode, done.stdout, done.stderr))
        return runs


def statuses(stdout, texts):
    """({text: "P" or "F"} for each automated line the run printed, [texts it printed that gate.json doesn't name],
    [known texts it printed without a measured value])."""
    found, undeclared, unmeasured = {}, [], []
    for line in stdout.splitlines():
        status, _, rest = line.partition(" ")
        if status not in STATUS:
            continue
        # Matched on the known texts, longest first, so a text holding parentheses still splits from its measured
        # value, and a text that starts with another's isn't counted as both.
        matches = [text for text in texts if rest.startswith(text + " (") and rest.endswith(")")]
        if matches:
            found[max(matches, key=len)] = STATUS[status]
        elif rest in texts:
            found[rest] = STATUS[status]
            unmeasured.append(rest)
        else:
            undeclared.append(rest.rpartition(" (")[0] or rest)
    return found, undeclared, unmeasured


def environment_problems(case, runs):
    """One line per exit code other than 0 or 1, naming the reruns that gave it and the last thing they said."""
    out = []
    for code in sorted({code for code, _, _ in runs} - {0, 1}):
        numbers = [i for i, (c, _, _) in enumerate(runs, 1) if c == code]
        said = [line for line in runs[numbers[0] - 1][2].splitlines() if line.strip()]
        out.append(f"Environment problem: {describe(case)} exits {code} on {which_runs(numbers)}" + (f": {said[-1]}" if said else ""))
    return out


def exit_mismatches(case, runs, found):
    """One line per exit code, 0 or 1, that the run's printed lines contradict, as exercise-format.md's exit table defines.

    A learner reads the exit code alone, so an Exercise check exiting 0 on a failed line passes an unsolved Exercise.
    """
    out = []
    for code, reason in ((0, "though a line failed"), (1, "though every line passed")):
        numbers = [
            i for i, ((c, _, _), lines) in enumerate(zip(runs, found), 1)
            if c == code and lines and ("F" in lines.values()) == (code == 0)
        ]
        if numbers:
            out.append(f"Broken: {describe(case)} exits {code} on {which_runs(numbers)} {reason}")
    return out


def which_runs(numbers):
    return f"run {numbers[0]}" if len(numbers) == 1 else "runs " + ", ".join(map(str, numbers))


def expected(line, case, manifest):
    """"P" or "F", what the line must show on the case, or None when the case doesn't bind it."""
    if line["kind"] == "guard":
        return "P" if case == "reference" else None
    if case == "starter":
        return "F"
    if case == "reference":
        return "P"
    return "F" if manifest["near_misses"][case] == line["text"] else None


def broken(line, results, manifest):
    """Why the line breaks the gate's rules, one reason per case."""
    reasons = []
    for case, runs in results.items():
        # A run with an environment problem (None) says nothing about the line, so the others are judged without it.
        seen = [run.get(line["text"], "-") for run in runs if run is not None]
        if not seen:
            continue
        if "-" in seen:
            reasons.append(f"isn't printed on {describe(case)}")
        elif len(set(seen)) > 1:
            reasons.append(f"gives different results across reruns on {describe(case)}")
        elif (want := expected(line, case, manifest)) and seen[0] != want:
            reasons.append(f"{'passes' if want == 'F' else 'fails'} on {describe(case)}")
    return reasons


def describe(case):
    return f"the {case}" if case in ("starter", "reference") else f"the Near-miss {case}"


def gate(exercise, gen):
    """The per-line matrix and the verdict, and the exit code: 0 pass, 1 a rule broken, 2 an environment problem.

    Each automated line gets one row: its kind, then one cell per case in the Cases order, holding one letter per
    rerun: P passed, F failed, - not printed, E the run had an environment problem and isn't judged.
    """
    manifest, cases = gate_cases(gen)
    automated = [line for line in manifest["lines"] if line["kind"] != "self-check"]
    texts = [line["text"] for line in automated]
    results, environment, case_problems = {}, [], []
    for name, swap in cases:
        runs = run_case(exercise, swap)
        # A run exiting other than 0 or 1 couldn't measure, so it holds no line's result.
        measured = [statuses(out, texts) if code in (0, 1) else (None, [], []) for code, out, _ in runs]
        results[name] = [found for found, _, _ in measured]
        printed = dict.fromkeys(text for _, extra, _ in measured for text in extra)
        bare = dict.fromkeys(text for _, _, unmeasured in measured for text in unmeasured)
        case_problems += [f"Broken: printed without a measured value in parentheses on {describe(name)}: {text}" for text in bare]
        case_problems += [f"Broken: printed on {describe(name)} but not in gate.json: {text}" for text in printed]
        case_problems += exit_mismatches(name, runs, results[name])
        environment += environment_problems(name, runs)
    out = ["Cases: " + ", ".join(name for name, _ in cases)]
    width = max((len(line["kind"]) for line in automated), default=0) + 2
    for line in automated:
        cells = " ".join(
            "".join("E" if run is None else run.get(line["text"], "-") for run in results[name]) for name, _ in cases
        )
        out.append(f"{line['kind']:<{width}}{cells}  {line['text']}")
    out.append("")
    problems = [f"Broken: {reason}: {line['text']}" for line in automated for reason in broken(line, results, manifest)]
    problems += case_problems
    out += environment + problems
    if environment:
        # Named apart from a line failure, so the author fixes the setup instead of revising lines.
        return "\n".join(out + ["Verdict: environment problem"]) + "\n", 2
    return "\n".join(out + ["Verdict: " + ("fail" if problems else "pass")]) + "\n", 1 if problems else 0


# --- CLI ---------------------------------------------------------------------


def main(argv=None):
    if build.FORMAT_VERSION != FORMAT_VERSION:
        print(
            f"exercises: Format version {FORMAT_VERSION} differs from build-curriculum's build.py, "
            f"which reads Format version {build.FORMAT_VERSION}; update both skills together",
            file=sys.stderr,
        )
        return 1
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("context", help="print the Subsection and its Prereq closure")
    p.add_argument("id")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p = sub.add_parser("existing", help="list the Subsection's Exercises and the next <NN>")
    p.add_argument("id")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--practice", help="the Practice workspace (default: practice/ in the Curriculums directory)")
    p = sub.add_parser("gate", help="run the Exercise check on every case and judge its lines")
    p.add_argument("exercise", type=Path, help="the Exercise, as it would ship")
    p.add_argument("gen", type=Path, help="the generation directory holding gate.json, reference/ and near-misses/")
    args = parser.parse_args(argv)

    try:
        if args.command == "context":
            sys.stdout.write(context(Path(args.curriculums), args.id))
        elif args.command == "gate":
            report, code = gate(args.exercise, args.gen)
            sys.stdout.write(report)
            return code
        else:
            practice = Path(args.practice) if args.practice else Path(args.curriculums) / "practice"
            sys.stdout.write(existing(practice, args.id))
    except BuildError as e:
        for line in str(e).split("\n"):
            print(f"{args.command}: {line}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"{args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
