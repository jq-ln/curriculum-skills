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

Reads doc sets through build-curriculum's build.py, so both skills parse a
Curriculum one way. FORMAT_VERSION is kept in step with ../references/curriculum-format.md,
and the script refuses to run when build.py's differs. Standard library only.
"""

import argparse
import re
import sys
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


def existing(practice, token):
    """The anchor's Exercises, lowest <NN> first, then the next <NN>."""
    uid = subsection_id(token)
    code_dir = Path(practice) / uid.code
    found = exercise_numbers(code_dir, uid)
    return "\n".join(sorted(found, key=found.get) or ["None"]) + f"\nNext: {next_number(code_dir, uid):02d}\n"


# --- renumber ----------------------------------------------------------------

EXERCISE = "EXERCISE.md"
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
    path = Path(exercise_dir) / EXERCISE
    if not path.is_file():
        return f"no {EXERCISE}"
    try:
        text = build.read(path)
    except (BuildError, OSError):
        return f"{EXERCISE} can't be read"
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
    _, units = anchor_units(directory, token)

    path = exercise_dir / EXERCISE
    lines = path.read_bytes().decode("utf-8").split("\n")  # anchor_record has checked it decodes
    at = record_lines("\n".join(line.removesuffix("\r") for line in lines))
    for key, value in (("Anchor", new), ("Anchor title", units[new].title)):
        ending = "\r" if lines[at[key]].endswith("\r") else ""  # so a CRLF file stays CRLF
        lines[at[key]] = f"- {key}: {value}{ending}"
    path.write_bytes("\n".join(lines).encode("utf-8"))

    if old == new:
        return f"renamed: {name} → {name}\n"
    slug = EXERCISE_NAME_RE.fullmatch(name)[3]
    new_name = f"{new}-{next_number(exercise_dir.parent, new):02d}-{slug}"
    exercise_dir.rename(exercise_dir.parent / new_name)
    return f"renamed: {name} → {new_name}\n"


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
    p = sub.add_parser("renumber", help="report whether each of the Curriculum's Exercises still names its anchor")
    p.add_argument("code")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--practice", help="the Practice workspace (default: practice/ in the Curriculums directory)")
    p = sub.add_parser("rename", help="point an Exercise at a new anchor, once the learner has confirmed it")
    p.add_argument("exercise", help="the Exercise's directory")
    p.add_argument("id", help="the new anchor's Subsection ID")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    args = parser.parse_args(argv)

    try:
        if args.command == "context":
            sys.stdout.write(context(Path(args.curriculums), args.id))
        elif args.command == "rename":
            sys.stdout.write(rename(Path(args.curriculums), Path(args.exercise), args.id))
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
