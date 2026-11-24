#!/usr/bin/env python3
"""Do the deterministic jobs of build-exercises.

Subcommands:
  context <ID> [--curriculums <dir>]  print the Subsection and its Prereq closure
  existing <ID> [--curriculums <dir>] [--practice <dir>]
                                      list the Subsection's Exercises and the next <NN>
  renumber <CODE> [--curriculums <dir>] [--practice <dir>]
                                      report each Exercise as valid, moved or broken; writes nothing
  rename <exercise dir> <ID> [--curriculums <dir>]
                                      point an Exercise at a new anchor, once the learner confirms
  assets <domain> <gen-dir> --exercise-name <ID>-<NN>-<slug> [--curriculums <dir>] [--domains <dir>]
                                      fill a Domain reference's assets/ into a Generation directory
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

DOMAINS = Path(__file__).resolve().parents[1] / "references" / "domains"
TEMPLATE_SUFFIX = ".tmpl"
PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")
# A name assets will fill: a Subsection-shaped ID and a well-formed slug.
NEW_EXERCISE_NAME_RE = re.compile(rf"(?P<id>{build.CODE}-[0-9.]+)-[0-9]{{2,}}-[a-z0-9]+(?:-[a-z0-9]+)*")


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
    """(UnitId, {UnitId: Unit}, its Curriculum's directory). Raises BuildError when the anchor can't be read."""
    uid = subsection_id(token)
    root = curriculum_dir(directory, uid.code)
    if isinstance(root, str):
        raise BuildError(root)
    units = build.doc_set_subsections(root)  # its errors are printed in full: this run can't go on without them fixed
    if uid not in units:
        raise BuildError(f"{token} names no Subsection in {root.name}")
    return uid, units, root


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
    anchor, units, _ = anchor_units(directory, token)
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


# --- assets ------------------------------------------------------------------


def target_version(root):
    """The Curriculum's Target version, or "" when its index has none."""
    field = build.parse(build.read(Path(root) / "index.md")).field("Target version")
    return field.body().strip() if field else ""


def fill(path, rel, values):
    """A template's text with each placeholder filled. Raises BuildError on any placeholder not in values."""
    try:
        text = path.read_bytes().decode("utf-8")  # bytes, so CRLF line endings survive filling
    except UnicodeDecodeError:
        raise BuildError(f"{rel}: a template must be UTF-8 text")
    for n, line in enumerate(text.split("\n"), 1):
        for name in PLACEHOLDER_RE.findall(line):
            if name not in values:
                known = " and ".join(f"{{{{{k}}}}}" for k in values)
                raise BuildError(f"{rel}:{n}: unknown placeholder {{{{{name}}}}}; only {known} are filled")
    return PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], text)


def assets(domains, domain, gen_dir, exercise_name, directory):
    """Mirror the domain's assets/ into gen_dir, filling *.tmpl files. Returns the written paths, relative to gen_dir.

    Checks everything before writing, so an error leaves gen_dir as it was.
    """
    m = NEW_EXERCISE_NAME_RE.fullmatch(exercise_name)
    if not m:
        raise BuildError(f"{exercise_name} isn't an Exercise name, <ID>-<NN>-<slug>")
    _, _, root = anchor_units(directory, m.group("id"))
    values = {"target_version": target_version(root), "exercise_name": exercise_name}

    source = domains / domain / "assets"
    if not source.is_dir():
        found = sorted(d.name for d in domains.iterdir() if (d / "assets").is_dir()) if domains.is_dir() else []
        raise BuildError(f"no Domain reference {domain} in {domains.resolve()}; found: {', '.join(found) or 'none'}")
    if not (source / f"check.sh{TEMPLATE_SUFFIX}").is_file():
        raise BuildError(f"{domain}: assets/check.sh{TEMPLATE_SUFFIX} is missing; every Domain reference needs it")
    if gen_dir.exists() and (not gen_dir.is_dir() or any(gen_dir.iterdir())):
        raise BuildError(f"{gen_dir} isn't an empty directory; assets fills a fresh Generation directory")

    planned = {}  # destination, relative to gen_dir -> (source file, filled text or None for a byte-for-byte copy)
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = path.relative_to(source)
        if rel.name.endswith(TEMPLATE_SUFFIX) and rel.name != TEMPLATE_SUFFIX:
            dest, content = rel.with_name(rel.name[: -len(TEMPLATE_SUFFIX)]), fill(path, rel, values)
        else:
            dest, content = rel, None
        if dest in planned:
            raise BuildError(f"{rel}: fills {dest}, which {planned[dest][0].relative_to(source)} also writes")
        planned[dest] = (path, content)

    for rel in sorted(p.relative_to(source) for p in source.rglob("*") if p.is_dir()):
        (gen_dir / rel).mkdir(parents=True, exist_ok=True)  # an empty directory may be where a starter's files go
    for dest, (path, content) in planned.items():
        out = gen_dir / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            shutil.copyfile(path, out)
        else:
            out.write_bytes(content.encode("utf-8"))
        shutil.copymode(path, out)  # keeps check.sh executable
    return sorted(planned, key=lambda p: p.as_posix())  # as `LC_ALL=C sort` orders them


# --- existing ----------------------------------------------------------------


# Any slug, even an empty one, so a misnamed Exercise still holds its number.
EXERCISE_NAME_RE = re.compile(rf"({build.CODE}-[0-9]{{2}}\.[0-9]{{2}}\.[0-9]{{2}})-([0-9]{{2,}})-(.*)")


def exercise_numbers(code_dir, uid):
    """{Exercise name: <NN>} for each of the anchor's Exercises in code_dir."""
    out = {}
    if Path(code_dir).is_dir():
        for d in Path(code_dir).iterdir():
            m = EXERCISE_NAME_RE.fullmatch(d.name)
            if m and m[1] == str(uid) and d.is_dir():
                out[d.name] = int(m[2])
    return out


def exercise_name_id(name):
    """The anchor ID an Exercise's directory name starts with, or None when it isn't named <ID>-<NN>-<slug>."""
    m = EXERCISE_NAME_RE.fullmatch(name)
    return build.parse_id(m[1]) if m else None


def next_number(code_dir, uid):
    """The highest <NN> plus one, never a gap's number, so a deleted Exercise's number isn't reused."""
    return max(exercise_numbers(code_dir, uid).values(), default=0) + 1


EXERCISE = "EXERCISE.md"
MARKER = "Your code goes here."
# The sections that, with the markers, say what an Exercise covered, so the ramp needs no record of its own.
COVERED_SECTIONS = ["Done when", "Given"]
# The rest of what an Exercise ships, so a marker quoted in a hint or the Exercise check isn't counted as the starter's.
NOT_STARTER = {EXERCISE, "check.sh", "check", "hints"}


def read_exercise_md(exercise_dir):
    """(EXERCISE.md's text, None), or (None, why) when the Exercise has none or it can't be read."""
    path = Path(exercise_dir) / EXERCISE
    if not path.is_file():
        return None, f"no {EXERCISE}"
    try:
        return build.read(path), None
    except (BuildError, OSError):
        return None, f"{EXERCISE} can't be read"


def sections(text):
    """(H1 text, {H2 heading: body lines, blank lines at either end dropped})."""
    title, out, body, fenced = None, {}, None, False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced  # a `## ` line in a fenced block, such as a sample in Given, isn't a heading
        if not fenced and line.startswith("# ") and title is None and not out:
            title = line[2:].strip()
        elif not fenced and line.startswith("## "):
            body = out.setdefault(line[3:].strip(), [])
        elif body is not None:
            body.append(line.rstrip())
    for lines in out.values():
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
    return title, out


def markers(exercise_dir):
    """`<path>:<line>` of each marker in the starter, in path order. A learner may have removed some."""
    out = []
    for path in sorted(p for p in Path(exercise_dir).rglob("*") if p.is_file()):
        rel = path.relative_to(exercise_dir)
        # A hidden path is the tool's or the learner's, such as Godot's .godot/ cache, never the starter's.
        if rel.parts[0] in NOT_STARTER or any(part.startswith(".") for part in rel.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue  # a binary file, such as an image, holds no marker
        out += [f"{rel.as_posix()}:{i}" for i, line in enumerate(lines, 1) if MARKER in line]
    return out


def covered(exercise_dir):
    """The indented lines existing prints under an Exercise: what it covered, read from its files."""
    text, why = read_exercise_md(exercise_dir)
    if why:
        return [f"  {why}"]
    title, found = sections(text)
    out = [f"  Title: {title}" if title else "  Title: none"]
    for heading in COVERED_SECTIONS:
        body = found.get(heading)
        out += [f"  {heading}:"] + [f"    {line}" if line else "" for line in body] if body else [f"  {heading}: none"]
    spots = markers(exercise_dir)
    return out + (["  Markers:"] + [f"    {spot}" for spot in spots] if spots else ["  Markers: none"])


def existing(practice, token):
    """The anchor's Exercises, lowest <NN> first, each with what it covered, then the next <NN>."""
    uid = subsection_id(token)
    code_dir = Path(practice) / uid.code
    found = exercise_numbers(code_dir, uid)
    lines = [line for name in sorted(found, key=found.get) for line in [name, *covered(code_dir / name)]]
    return "\n".join(lines or ["None"]) + f"\nNext: {next_number(code_dir, uid):02d}\n"


# --- renumber ----------------------------------------------------------------

RECORD_KEYS = ["Curriculum", "Anchor", "Anchor title"]  # the anchor record's bullets renumber needs


def record_lines(text):
    """{key: line index} for the anchor record's bullets: the `- <key>: <value>` lines straight after the H1."""
    lines = text.split("\n")
    h1 = next((i for i, line in enumerate(lines) if line.strip()), None)
    if h1 is None or not lines[h1].startswith("# "):
        return {}
    out = {}
    for i in range(h1 + 1, len(lines)):
        if not lines[i].strip() and not out:
            continue
        key, sep, _ = lines[i].removeprefix("- ").partition(": ")
        if not lines[i].startswith("- ") or not sep:
            break
        out.setdefault(key, i)
    return out


def anchor_record(exercise_dir, code):
    """(UnitId, anchor title) from an Exercise's anchor record, or a string saying why it can't be read."""
    text, why = read_exercise_md(exercise_dir)
    if why:
        return why
    lines = text.split("\n")
    record = {key: lines[i].partition(": ")[2] for key, i in record_lines(text).items()}
    uid = build.parse_id(record.get("Anchor", ""))
    if any(key not in record for key in RECORD_KEYS) or not uid or len(uid.levels) != 3:
        return f"{EXERCISE} has no anchor record"
    if record["Curriculum"] != code:
        return f"{EXERCISE} records Curriculum {record['Curriculum']}"
    if uid.code != code:
        return f"{EXERCISE} records anchor {uid}, outside {code}"
    return uid, record["Anchor title"]


def status(exercise_dir, units, code):
    """The lines renumber prints for one Exercise."""
    name = Path(exercise_dir).name
    record = anchor_record(exercise_dir, code)
    if isinstance(record, str):
        return [f"{name}: broken: {record}"]
    uid, title = record
    titled = [u for u in sorted(units, key=lambda u: u.levels) if units[u].title == title]
    found = uid if uid in titled else titled[0] if len(titled) == 1 else None
    # The record and the name must both agree with the anchor. Either can lag, as when a rename stops between
    # rewriting the record and renaming the directory, and the lagging one gives the old ID.
    named = exercise_name_id(name)
    if found and found == named == uid:
        return [f"{name}: valid"]
    if found:
        return [f"{name}: moved: {uid if uid != found else named} → {found}"]
    if titled:
        out = [f'{name}: broken: {len(titled)} Subsections are titled "{title}"']
    else:
        out = [f'{name}: broken: no Subsection is titled "{title}"']
        # A retitle keeps the ID, so the Subsection there is the likely anchor, but only the learner can say so.
        titled = [uid] if uid in units else []
    return out + [f"  candidate: {u} {units[u].title}" for u in titled]


def renumber(directory, practice, code):
    """Whether each of the Curriculum's Exercises is valid, moved or broken, in name order. Writes nothing."""
    root = curriculum_dir(directory, code)
    if isinstance(root, str):
        raise BuildError(root)
    units = build.doc_set_subsections(root)
    code_dir = Path(practice) / code
    dirs = sorted(d for d in code_dir.iterdir() if d.is_dir()) if code_dir.is_dir() else []
    # Only Exercises of this code, so a generation directory or a learner's own folder isn't reported as broken.
    dirs = [d for d in dirs if (uid := exercise_name_id(d.name)) and uid.code == code]
    return "\n".join([line for d in dirs for line in status(d, units, code)] or ["None"]) + "\n"


# --- rename ------------------------------------------------------------------


def rename(directory, exercise_dir, token):
    """Point an Exercise at a new anchor: rewrite its anchor record, then rename its directory.

    Run only once the learner has confirmed the move. The slug stays, and the <NN> is the next
    free one under the new ID, so the renamed Exercise never collides with one already there.
    """
    exercise_dir = Path(exercise_dir).resolve()  # so `rename . <ID>` from inside the Exercise has a name to read
    name = exercise_dir.name
    if not exercise_dir.is_dir():
        raise BuildError(f"{name} isn't a directory")
    old = exercise_name_id(name)
    if not old:
        raise BuildError(f"{name} isn't named <ID>-<NN>-<slug>")
    code = old.code
    record = anchor_record(exercise_dir, code)
    if isinstance(record, str):
        raise BuildError(f"{name}: {record}")
    new = subsection_id(token)
    if new.code != code:
        raise BuildError(f"{new} isn't in Curriculum {code}")
    _, units, _ = anchor_units(directory, token)

    path = exercise_dir / EXERCISE
    # Split on the same line endings build.read's read_text does, keeping each one, so the line
    # numbers agree with anchor_record's and every line keeps its own ending.
    parts = re.split(r"(\r\n|\r|\n)", path.read_bytes().decode("utf-8"))  # anchor_record has checked it decodes
    lines, endings = parts[0::2], parts[1::2] + [""]
    at = record_lines("\n".join(lines))
    for key, value in (("Anchor", new), ("Anchor title", units[new].title)):
        lines[at[key]] = f"- {key}: {value}"
    path.write_bytes("".join(line + ending for line, ending in zip(lines, endings)).encode("utf-8"))

    if old == new:
        return f"renamed: {name} → {name}\n"
    slug = EXERCISE_NAME_RE.fullmatch(name)[3]
    new_name = f"{new}-{next_number(exercise_dir.parent, new):02d}-{slug}"
    exercise_dir.rename(exercise_dir.parent / new_name)
    return f"renamed: {name} → {new_name}\n"


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
    p = sub.add_parser("existing", help="list the Subsection's Exercises, what each covered, and the next <NN>")
    p.add_argument("id")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--practice", help="the Practice workspace (default: practice/ in the Curriculums directory)")
    p = sub.add_parser("renumber", help="report whether each of the Curriculum's Exercises still names its anchor")
    p.add_argument("code")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--practice", help="the Practice workspace (default: practice/ in the Curriculums directory)")
    p = sub.add_parser("rename", help="point an Exercise at a new anchor, once the learner has confirmed it")
    p.add_argument("exercise", help="the Exercise's directory")
    p.add_argument("id", help="the new anchor's Subsection ID")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p = sub.add_parser("assets", help="fill a Domain reference's assets/ into a Generation directory")
    p.add_argument("domain")
    p.add_argument("gen_dir")
    p.add_argument("--exercise-name", required=True, help="<ID>-<NN>-<slug>, filled as {{exercise_name}}")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--domains", default=DOMAINS, help="the directory holding the Domain references (default: the skill's)")
    p = sub.add_parser("gate", help="run the Exercise check on every case and judge its lines")
    p.add_argument("exercise", type=Path, help="the Exercise, as it would ship")
    p.add_argument("gen", type=Path, help="the generation directory holding gate.json, reference/ and near-misses/")
    args = parser.parse_args(argv)

    try:
        if args.command == "context":
            sys.stdout.write(context(Path(args.curriculums), args.id))
        elif args.command == "rename":
            sys.stdout.write(rename(Path(args.curriculums), Path(args.exercise), args.id))
        elif args.command == "assets":
            for rel in assets(Path(args.domains), args.domain, Path(args.gen_dir), args.exercise_name, Path(args.curriculums)):
                print(rel.as_posix())
        elif args.command == "gate":
            report, code = gate(args.exercise, args.gen)
            sys.stdout.write(report)
            return code
        else:
            practice = Path(args.practice) if args.practice else Path(args.curriculums) / "practice"
            if args.command == "existing":
                sys.stdout.write(existing(practice, args.id))
            else:
                sys.stdout.write(renumber(Path(args.curriculums), practice, args.code))
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
