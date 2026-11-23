#!/usr/bin/env python3
"""Do the deterministic jobs of build-exercises.

Subcommands:
  context <ID> [--curriculums <dir>]  print the Subsection and its Prereq closure
  existing <ID> [--curriculums <dir>] [--practice <dir>]
                                      list the Subsection's Exercises and the next <NN>

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


def existing(practice, token):
    """The anchor's Exercises, lowest <NN> first, then the next <NN>."""
    uid = subsection_id(token)
    exercise = re.compile(rf"{re.escape(str(uid))}-([0-9]{{2,}})-.+")
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
    args = parser.parse_args(argv)

    try:
        if args.command == "context":
            sys.stdout.write(context(Path(args.curriculums), args.id))
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
