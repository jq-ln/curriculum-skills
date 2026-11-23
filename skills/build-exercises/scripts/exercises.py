#!/usr/bin/env python3
"""Do the deterministic jobs of build-exercises.

Subcommands:
  context <ID> [--curriculums <dir>]  print the Subsection and its Prereq closure
  assets <domain> <gen-dir> --exercise-name <ID>-<NN>-<slug> [--curriculums <dir>] [--domains <dir>]
                                      fill a domain reference's assets/ into a generation directory

Reads doc sets through build-curriculum's build.py, so both skills parse a
Curriculum one way. FORMAT_VERSION is kept in step with ../references/curriculum-format.md,
and the script refuses to run when build.py's differs. Standard library only.
"""

import argparse
import re
import shutil
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

DOMAINS = Path(__file__).resolve().parents[1] / "references" / "domains"
TEMPLATE_SUFFIX = ".tmpl"
PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")
EXERCISE_NAME_RE = re.compile(rf"(?P<id>{build.CODE}-[0-9.]+)-(?P<nn>[0-9]{{2,}})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)")


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


def anchor_units(directory, token):
    """(UnitId, {UnitId: Unit}) for the anchor's Curriculum. Raises BuildError when the anchor can't be read."""
    uid = build.parse_id(token)
    if not uid:
        raise BuildError(f"{token} isn't an ID")
    if len(uid.levels) != 3:
        raise BuildError(f"{token} isn't a Subsection ID")
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


# --- assets ------------------------------------------------------------------


def target_version(root):
    """The Curriculum's Target version, or "" when its index has none."""
    field = build.parse(build.read(Path(root) / "index.md")).field("Target version")
    return field.body().strip() if field else ""


def fill(path, rel, values):
    """A template's text with each placeholder filled. Raises BuildError on any placeholder not in values."""
    try:
        text = path.read_text(encoding="utf-8")
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
    m = EXERCISE_NAME_RE.fullmatch(exercise_name)
    if not m:
        raise BuildError(f"{exercise_name} isn't an Exercise name, <ID>-<NN>-<slug>")
    uid, _ = anchor_units(directory, m.group("id"))
    root = curriculum_dir(directory, uid.code)
    values = {"target_version": target_version(root), "exercise_name": exercise_name}

    source = Path(domains) / domain / "assets"
    if not source.is_dir():
        found = sorted(d.name for d in Path(domains).iterdir() if (d / "assets").is_dir()) if Path(domains).is_dir() else []
        raise BuildError(f"no domain reference {domain} in {Path(domains).resolve()}; found: {', '.join(found) or 'none'}")
    if not (source / f"check.sh{TEMPLATE_SUFFIX}").is_file():
        raise BuildError(f"{domain}: assets/check.sh{TEMPLATE_SUFFIX} is missing; every domain reference needs it")
    gen_dir = Path(gen_dir)
    if gen_dir.exists() and (not gen_dir.is_dir() or any(gen_dir.iterdir())):
        raise BuildError(f"{gen_dir} isn't an empty directory; assets fills a fresh generation directory")

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

    for dest, (path, content) in planned.items():
        out = gen_dir / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            shutil.copyfile(path, out)
        else:
            out.write_text(content, encoding="utf-8", newline="")
        shutil.copymode(path, out)  # keeps check.sh executable
    return sorted(planned, key=lambda p: p.as_posix())  # as `LC_ALL=C sort` orders them


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
    p = sub.add_parser("assets", help="fill a domain reference's assets/ into a generation directory")
    p.add_argument("domain")
    p.add_argument("gen_dir")
    p.add_argument("--exercise-name", required=True, help="<ID>-<NN>-<slug>, filled as {{exercise_name}}")
    p.add_argument("--curriculums", default=".", help="the directory holding the Curriculums (default: the working directory)")
    p.add_argument("--domains", default=DOMAINS, help="the directory holding the domain references (default: the skill's)")
    args = parser.parse_args(argv)

    try:
        if args.command == "context":
            sys.stdout.write(context(Path(args.curriculums), args.id))
        else:
            for rel in assets(Path(args.domains), args.domain, Path(args.gen_dir), args.exercise_name, Path(args.curriculums)):
                print(rel.as_posix())
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
