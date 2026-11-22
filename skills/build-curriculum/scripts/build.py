#!/usr/bin/env python3
"""Build a Curriculum doc set from a Draft, derive its copies and check it.

Subcommands:
  split <draft-dir> <output-dir>  write the doc set from a Draft
  derive <doc-set-dir>            rewrite derived content in place
  check <doc-set-dir>             print one line per error; exit 1 if any

Follows the curriculum format in ../references/curriculum-format.md, which this
script never reads: FORMAT_VERSION and the rules below are kept in step with it,
and CI fails when FORMAT_VERSION drifts. Standard library only.

Appendices are recognised by filename and H1 only: split doesn't take them from
a Draft, check doesn't check their Fields, and derive leaves them as they are.
"""

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path

FORMAT_VERSION = 1

# Doc types, as the format doc names them.
INDEX = "Index"
OVERVIEW = "Overview"
TAGS = "Tags doc"
SOURCES = "Sources doc"
NOTES = "Notes doc"
PART = "Part"
SECTION = "Section"
SUBSECTION = "Subsection"
APPENDIX = "Appendix"
UNIT_TYPES = {1: PART, 2: SECTION, 3: SUBSECTION}

# Each Doc type's Fields in their fixed order, with whether each is required.
# Fields this script doesn't derive yet are left out, so writing one by hand is
# an unknown-Field error rather than content the script silently ignores.
FIELDS = {
    INDEX: [("Intro", True), ("Snapshot", True), ("Target version", False), ("Format version", True)],
    OVERVIEW: [("Methodology", True), ("Ordering rationale", True)],
    TAGS: [],
    SOURCES: [("Families", True), ("Abbreviations", True)],
    NOTES: [
        ("Judgement calls", True),
        ("Scope decisions", True),
        ("Ordering and granularity choices", True),
        ("Build notes", True),
        ("Open questions", False),
    ],
    PART: [("Intro", True)],
    SECTION: [("Generators", True)],
    SUBSECTION: [
        ("Context", True),
        ("Goal", True),
        ("Generators", False),
        ("Foundations", False),
        ("Scope", True),
        ("Key concepts", True),
        ("Prereqs", True),
        ("Check", True),
        ("Sources", True),
    ],
    APPENDIX: [],  # its Fields aren't read yet, so every H2 in it is free content
}
# Fields derive writes. A missing one isn't a Field error: derive adds it, and check reports it
# as derived content that differs from what derive writes.
DERIVED_FIELDS = {"Context"}
# Doc types whose H2s after their Fields are free content. In the tags doc every H2 is a tag.
FREE_H2 = {NOTES, APPENDIX}

CODE = r"[A-Z][A-Z0-9]*"
ID_RE = re.compile(rf"({CODE})-([0-9]{{2}})(?:\.([0-9]{{2}}))?(?:\.([0-9]{{2}}))?")
INDEX_H1_RE = re.compile(rf"(.+) \(({CODE})\)")
NAMED_H1_RE = re.compile(rf"({CODE}) (Overview|Tags|Sources|Notes)")
NAMED_TYPES = {"Overview": OVERVIEW, "Tags": TAGS, "Sources": SOURCES, "Notes": NOTES}
APPENDIX_H1_RE = re.compile(rf"({CODE}) Appendix: (.+)")
DESCRIPTION = r"[a-z0-9]+(?:-[a-z0-9]+)*"
HEADING_RE = re.compile(r"(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*")
FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})")
SETEXT_RE = re.compile(r" {0,3}(=+|-+)[ \t]*")
# Lines that start a block other than a paragraph, so a `---` under them is a thematic break.
NON_PARAGRAPH_RE = re.compile(r" {0,3}([-+*]|[0-9]{1,9}[.)])([ \t]|$)| {0,3}[>|<]")
# HTML blocks of CommonMark types 1-5, which run to their end marker, blank lines included:
# (start pattern, end pattern).
HTML_BLOCKS = [
    (re.compile(r" {0,3}<(pre|script|style|textarea)([ \t>]|$)", re.I), re.compile(r"</(pre|script|style|textarea)>", re.I)),
    (re.compile(r" {0,3}<!--"), re.compile(r"-->")),
    (re.compile(r" {0,3}<\?"), re.compile(r"\?>")),
    (re.compile(r" {0,3}<![A-Za-z]"), re.compile(r">")),
    (re.compile(r" {0,3}<!\[CDATA\["), re.compile(r"\]\]>")),
]
MARKSMAN = ".marksman.toml"
# Deriving copies titles unescaped into link text and table rows, which these would break.
FORBIDDEN_IN_TITLE = "[]|\\<&`"


class BuildError(Exception):
    """A problem that stops a subcommand before it writes anything."""


# --- Parsing -----------------------------------------------------------------


def heading(line):
    """(level, text) if line is a top-level ATX heading, else None.

    Only headings starting in column 0 count, which keeps a heading-like line in
    a list item out but also misses a top-level heading indented 1-3 spaces.
    """
    m = HEADING_RE.fullmatch(line.rstrip("\n"))
    if not m:
        return None
    return len(m.group(1)), m.group(2) or ""


def scan_lines(lines):
    """Yield (line, heading-or-None), skipping headings inside fenced code and HTML blocks.

    Raises BuildError on a setext heading. A paragraph is approximated as a run of
    non-blank lines that starts in column 0 and holds no list item, blockquote,
    table row, HTML or heading. Starting in column 0 keeps a list item's
    continuation paragraph out, but, as with heading(), misses a top-level
    paragraph indented 1-3 spaces.
    """
    fence = None
    html_end = None  # the end marker of the open HTML block, if any
    paragraph = None  # the current run of non-blank lines, while it can be a paragraph
    for line in lines:
        if html_end:
            if html_end.search(line):
                html_end = None
            yield line, None
            continue
        m = FENCE_RE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line[m.end():].strip():
                fence = None
            yield line, None
            continue
        if m and not (m.group(1)[0] == "`" and "`" in line[m.end():]):
            fence, paragraph = m.group(1), None
            yield line, None
            continue
        html = next(((start, end) for start, end in HTML_BLOCKS if start.match(line)), None)
        if html:
            start, end = html
            paragraph = None
            if not end.search(line, start.match(line).end()):
                html_end = end
            yield line, None
            continue
        h = heading(line)
        if not line.strip():
            paragraph = None
        elif paragraph and SETEXT_RE.fullmatch(line.rstrip("\n")):
            raise BuildError(f"has a setext heading, `{paragraph[-1].strip()}` over `{line.strip()}`; use an ATX heading")
        elif SETEXT_RE.fullmatch(line.rstrip("\n")) and "-" in line:
            paragraph = None  # a thematic break, which ends the block
        elif h or NON_PARAGRAPH_RE.match(line) or (paragraph is None and line.startswith(("    ", "\t"))):
            paragraph = False
        elif paragraph is None and line[0] in " \t":
            paragraph = False  # a list item's continuation, or a paragraph indented 1-3 spaces
        elif paragraph is not False:
            paragraph = (paragraph or []) + [line]
        yield line, h


@dataclass
class Block:
    """One H2 and its content, kept as raw lines so unchanged content round-trips."""

    name: str
    lines: list

    def body(self):
        return "".join(self.lines[1:]).strip("\n")


@dataclass
class Doc:
    front: list = dataclass_field(default_factory=list)  # front matter, delimiters included, and blank lines before the H1
    head: list = dataclass_field(default_factory=list)  # the H1 line, then any content before the first H2
    blocks: list = dataclass_field(default_factory=list)  # one Block per H2

    @property
    def h1(self):
        return self.head[0].rstrip("\n")[2:] if self.head else ""

    def field(self, name):
        return next((b for b in self.blocks if b.name == name), None)

    def text(self):
        out = "".join(self.front + self.head + [line for b in self.blocks for line in b.lines])
        return out.rstrip("\n") + "\n"


def parse(text):
    """Parse one doc. Raises BuildError when it doesn't start with an H1."""
    lines = text.splitlines(keepends=True)
    doc = Doc()
    if lines and lines[0].rstrip("\n") == "---":
        end = next((i for i, line in enumerate(lines[1:], 1) if line.rstrip("\n") == "---"), None)
        if end is not None:
            doc.front, lines = lines[: end + 1], lines[end + 1 :]
    while lines and not lines[0].strip():
        doc.front.append(lines[0])
        lines = lines[1:]
    for line, h in scan_lines(lines):
        if not doc.head:
            if not h or h[0] != 1:
                raise BuildError("doesn't start with an H1")
            doc.head.append(line)
        elif h and h[0] == 1:
            raise BuildError("has more than one H1")
        elif h and h[0] == 2:
            doc.blocks.append(Block(h[1], [line]))
        elif doc.blocks:
            doc.blocks[-1].lines.append(line)
        else:
            doc.head.append(line)
    if not doc.head:
        raise BuildError("doesn't start with an H1")
    return doc


def read(path):
    """A file's text. Raises BuildError when it isn't UTF-8 or starts with a byte order mark."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise BuildError("isn't valid UTF-8") from None
    if text.startswith("\ufeff"):
        raise BuildError("starts with a byte order mark; save it as UTF-8 without one")
    return text


def split_draft(text):
    """Split a Draft file into one Doc per top-level H1."""
    docs, chunk = [], []
    for line, h in scan_lines(text.splitlines(keepends=True)):
        if h and h[0] == 1 and "".join(chunk).strip():
            docs.append(parse("".join(chunk)))
            chunk = []
        chunk.append(line)
    if "".join(chunk).strip():
        docs.append(parse("".join(chunk)))
    return docs


# --- IDs, titles and filenames ---------------------------------------------


@dataclass(frozen=True)
class UnitId:
    code: str
    levels: tuple  # ints, one per level

    def __str__(self):
        return self.code + "-" + ".".join(f"{n:02d}" for n in self.levels)

    @property
    def doc_type(self):
        return UNIT_TYPES[len(self.levels)]

    def parent(self):
        return UnitId(self.code, self.levels[:-1])


def parse_id(text):
    """The UnitId text is exactly, or None. A level of 00 isn't an ID."""
    m = ID_RE.fullmatch(text)
    if not m:
        return None
    levels = tuple(int(g) for g in m.groups()[1:] if g is not None)
    return None if 0 in levels else UnitId(m.group(1), levels)


def not_an_id(text):
    return f"{text} isn't an ID: each level is two digits from 01 to 99"


def split_unit_h1(h1):
    """(UnitId, raw title) from a unit H1 `<ID> <title>`, or None."""
    token, _, title = h1.partition(" ")
    uid = parse_id(token)
    return (uid, title) if uid and title else None


def slug(title):
    """The format doc's slug rule: NFKD fold, separators, 60-character cap."""
    folded = "".join(c for c in unicodedata.normalize("NFKD", title) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    if len(s) > 60:
        head = s[:61]
        cut = head.rfind("-")
        s = head[:cut] if cut >= 0 else s[:60]
    return s


def title_errors(title, what="title"):
    """Why a unit title, or the Curriculum's name, can't be used, if it can't."""
    errors = []
    bad = sorted(set(title) & set(FORBIDDEN_IN_TITLE))
    if bad:
        errors.append(f"{what} contains {' '.join(bad)}, which would break a link or table copying it")
    if what == "title" and not slug(title):
        errors.append("title has an empty slug")
    return errors


def unit_filename(uid, title):
    return f"{uid}-{slug(title)}.md"


def doc_type_of_h1(h1):
    """(doc type, code, unit id or None) from a doc's H1 text, or None."""
    unit = split_unit_h1(h1)
    if unit:
        return unit[0].doc_type, unit[0].code, unit[0]
    m = NAMED_H1_RE.fullmatch(h1)
    if m:
        return NAMED_TYPES[m.group(2)], m.group(1), None
    m = INDEX_H1_RE.fullmatch(h1)
    if m:
        return INDEX, m.group(2), None
    return None


def filename_for(doc_type, code, h1):
    if doc_type == INDEX:
        return "index.md"
    if doc_type in (OVERVIEW, TAGS, SOURCES, NOTES):
        return f"{code}-{h1.split(' ', 1)[1].lower()}.md"
    uid, title = split_unit_h1(h1)
    return unit_filename(uid, title)


def field_index(doc_type, name):
    names = [n for n, _ in FIELDS[doc_type]]
    return names.index(name) if name in names else len(names)


# --- split -------------------------------------------------------------------


def split(draft_dir, out_dir):
    draft_dir, out_dir = Path(draft_dir), Path(out_dir)
    if not (draft_dir / "outline.md").is_file():
        raise BuildError(f"{draft_dir}: no outline.md")
    if out_dir.exists() and not out_dir.is_dir():
        raise BuildError(f"{out_dir}: already exists and isn't a directory")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise BuildError(f"{out_dir}: already exists and isn't empty")

    files = [draft_dir / "outline.md"] + sorted(draft_dir.glob("part-*.md"))
    merged = {}  # filename -> (doc type, Doc)
    keys = {}  # H1 key -> filename, so a part file's unit merges into the Outline's
    code = None
    for path in files:
        try:
            docs = split_draft(read(path))
        except BuildError as e:
            raise BuildError(f"{path.name}: {e}") from None
        for doc in docs:
            where = f"{path.name}: # {doc.h1}"
            kind = doc_type_of_h1(doc.h1)
            token = doc.h1.split(" ", 1)[0]
            if not kind and ID_RE.fullmatch(token):
                raise BuildError(f"{where}: {not_an_id(token)}")
            if not kind:
                raise BuildError(f"{where}: not the H1 of any Doc type")
            doc_type, doc_code, uid = kind
            if "".join(doc.head[1:]).strip():
                raise BuildError(f"{where}: has content before its first Field")
            if uid:
                errors = title_errors(split_unit_h1(doc.h1)[1])
            elif doc_type == INDEX:
                errors = title_errors(INDEX_H1_RE.fullmatch(doc.h1).group(1), "name")
            else:
                errors = []
            for error in errors:
                raise BuildError(f"{where}: {error}")
            if doc_type == INDEX:
                code = code or doc_code
            key = str(uid) if uid else doc_type
            if key not in keys:
                keys[key] = filename_for(doc_type, doc_code, doc.h1)
                merged[keys[key]] = (doc_type, Doc(head=[doc.head[0]]))
            _, into = merged[keys[key]]
            if into.h1 != doc.h1:
                raise BuildError(f"{where}: differs from the earlier H1 # {into.h1}")
            for block in doc.blocks:
                if block.name == "Format version":
                    raise BuildError(f"{where}: Format version is written by split, not the Draft")
                if into.field(block.name):
                    raise BuildError(f"{where}: Field {block.name} appears twice")
                into.blocks.append(block)

    if code is None:
        raise BuildError(f"{draft_dir}: the Draft has no index H1, `# <name> (<CODE>)`")
    for name, (doc_type, doc) in merged.items():
        _, doc_code, _ = doc_type_of_h1(doc.h1)
        if doc_code != code:
            raise BuildError(f"# {doc.h1}: code {doc_code} isn't the index's code {code}")
        if doc_type == INDEX:
            doc.blocks.append(Block("Format version", []))
        doc.blocks.sort(key=lambda b: field_index(doc_type, b.name))  # stable: free H2s keep their order

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (doc_type, doc) in merged.items():
        (out_dir / name).write_text(render(doc_type, doc), encoding="utf-8")
    (out_dir / MARKSMAN).write_text("", encoding="utf-8")


def render(doc_type, doc):
    """A Draft doc as a doc set doc: one blank line between blocks."""
    out = [doc.head[0], "\n"]
    for block in doc.blocks:
        body = str(FORMAT_VERSION) if block.name == "Format version" else block.body()
        out += [f"## {block.name}\n", "\n"] + ([body + "\n", "\n"] if body else [])
    return "".join(out).rstrip("\n") + "\n"


# --- Loading a doc set ---------------------------------------------------------


@dataclass
class DocSet:
    root: Path
    code: str = None
    docs: dict = dataclass_field(default_factory=dict)  # filename -> Doc
    types: dict = dataclass_field(default_factory=dict)  # filename -> doc type
    units: dict = dataclass_field(default_factory=dict)  # UnitId -> filename
    unit_ids: set = dataclass_field(default_factory=set)  # every UnitId a filename names, readable or not
    bad_unit_id: bool = False  # some unit filename has an ID that doesn't parse, so its place is unknown
    errors: list = dataclass_field(default_factory=list)  # (filename, message)

    def error(self, name, message):
        self.errors.append((name, message))

    def doc(self, uid):
        return self.docs[self.units[uid]]

    def title(self, uid):
        return split_unit_h1(self.doc(uid).h1)[1]


def load(root):
    """Read and classify every file in a doc set, collecting errors as it goes."""
    root = Path(root)
    ds = DocSet(root)
    index = root / "index.md"
    if not index.is_file():
        ds.error("index.md", "is missing")
        return ds
    try:
        doc = parse(read(index))
    except BuildError as e:
        ds.error("index.md", str(e))
        return ds
    m = INDEX_H1_RE.fullmatch(doc.h1)
    if not m:
        ds.error("index.md", f"H1 `# {doc.h1}` isn't `# <name> (<CODE>)`")
        return ds
    ds.code = m.group(2)
    for error in title_errors(m.group(1), "name"):
        ds.error("index.md", error)
    ds.docs["index.md"], ds.types["index.md"] = doc, INDEX

    named = {f"{ds.code}-{w.lower()}.md": (t, f"{ds.code} {w}") for w, t in NAMED_TYPES.items()}
    unit_name = re.compile(rf"({re.escape(ds.code)}-[0-9][0-9.]*)-(.+)\.md")
    appendix_name = re.compile(rf"{re.escape(ds.code)}-appendix-{DESCRIPTION}\.md")
    for path in sorted(root.iterdir()):
        name = path.name
        if name in ("index.md", MARKSMAN):
            continue
        if path.is_dir():
            ds.error(name, "is a subdirectory; a doc set is flat")
            continue
        m = unit_name.fullmatch(name)
        if name in named:
            (doc_type, h1), uid = named[name], None
        elif appendix_name.fullmatch(name):
            doc_type, h1, uid = APPENDIX, None, None
        elif m:
            uid = parse_id(m.group(1))
            if not uid:
                ds.error(name, not_an_id(m.group(1)))
                ds.bad_unit_id = True
                continue
            doc_type, h1 = uid.doc_type, None
            ds.unit_ids.add(uid)
        else:
            ds.error(name, "isn't a doc set filename")
            continue
        try:
            doc = parse(read(path))
        except BuildError as e:
            ds.error(name, str(e))
            continue
        if uid and not unit_h1_ok(ds, name, uid, doc):
            continue  # without a readable H1 the unit can't be placed or copied from
        if doc_type == APPENDIX and not appendix_h1_ok(ds, name, doc):
            continue
        if h1 and doc.h1 != h1:
            ds.error(name, f"H1 `# {doc.h1}` isn't `# {h1}`")
            continue
        ds.docs[name], ds.types[name] = doc, doc_type
        if uid:
            if uid in ds.units:
                ds.error(name, f"{uid} also names {ds.units[uid]}")
                continue
            ds.units[uid] = name
    for name in named:
        if not (root / name).exists():
            ds.error(name, "is missing")
    marksman = root / MARKSMAN
    if not marksman.exists():
        ds.error(MARKSMAN, "is missing")
    elif not marksman.is_file():
        ds.error(MARKSMAN, "isn't a file")
    elif marksman.stat().st_size:
        ds.error(MARKSMAN, "isn't empty")
    return ds


def unit_h1_ok(ds, name, uid, doc):
    """Check a unit's H1 against its filename, recording any error."""
    unit = split_unit_h1(doc.h1)
    if not unit:
        ds.error(name, f"H1 `# {doc.h1}` isn't `# <ID> <title>`")
        return False
    h1_id, title = unit
    if h1_id != uid:
        ds.error(name, f"H1 ID {h1_id} differs from the filename's ID {uid}")
        return False
    errors = title_errors(title)
    for error in errors:
        ds.error(name, error)
    if not errors and name != unit_filename(uid, title):
        ds.error(name, f"filename should be {unit_filename(uid, title)}, from its title")
    return True


def appendix_h1_ok(ds, name, doc):
    """Check an Appendix's H1, recording any error."""
    m = APPENDIX_H1_RE.fullmatch(doc.h1)
    if not m or m.group(1) != ds.code:
        ds.error(name, f"H1 `# {doc.h1}` isn't `# {ds.code} Appendix: <title>`")
        return False
    for error in title_errors(m.group(2), "Appendix title"):
        ds.error(name, error)
    return True


def format_version_errors(ds):
    """Errors for a missing or mismatched Format version, naming both numbers."""
    f = ds.docs["index.md"].field("Format version")
    if f is None:
        return [
            f"Format version is missing; this script reads Format version {FORMAT_VERSION}. "
            "Restore it from the history of index.md, such as `git log -p index.md`"
        ]
    body = f.body()
    if body != str(FORMAT_VERSION):
        shown = repr(body) if "\n" in body else body  # one line per error
        return [f"Format version is {shown}, but this script reads Format version {FORMAT_VERSION}"]
    return []


# --- derive ------------------------------------------------------------------


def derived(ds):
    """The new text of every doc whose derived content differs from what derive writes, by filename.

    Compares parsed text before and after, so a doc derive has nothing to change
    in is left alone, whitespace and all.
    """
    out = {}
    for name, doc in ds.docs.items():
        before = doc.text()
        if ds.types[name] == SUBSECTION:
            set_field(doc, SUBSECTION, "Context", context(ds, doc))
        if doc.text() != before:
            out[name] = doc.text()
    return out


def set_field(doc, doc_type, name, body):
    lines = [f"## {name}\n", "\n"] + [line + "\n" for line in body.split("\n")] + ["\n"]
    existing = doc.field(name)
    if existing:
        existing.lines = lines
        return
    at = next(
        (i for i, b in enumerate(doc.blocks) if field_index(doc_type, b.name) > field_index(doc_type, name)),
        len(doc.blocks),
    )
    doc.blocks.insert(at, Block(name, lines))
    if doc.head[-1].strip():
        doc.head.append("\n")


def context(ds, doc):
    index = ds.docs["index.md"]
    uid = split_unit_h1(doc.h1)[0]
    section, part = uid.parent(), uid.parent().parent()
    lines = [f"- Curriculum: {index.h1}"]
    target = index.field("Target version")
    if target:
        lines.append(f"- Target version: {target.body()}")
    lines.append(f"- Snapshot: {index.field('Snapshot').body()}")
    lines.append(f"- Part: [{part} {ds.title(part)}]({ds.units[part]})")
    lines.append(f"- Section: [{section} {ds.title(section)}]({ds.units[section]})")
    lines.append("- Section Generators:")
    generators = ds.doc(section).field("Generators").body()
    lines += ["  " + line if line.strip() else line for line in generators.split("\n")]
    return "\n".join(lines)


def derive(root):
    ds = load(root)
    errors = errors_before_derive(ds)
    if errors:
        raise BuildError("\n".join(f"{n}: {m}" for n, m in errors))
    for name, text in derived(ds).items():
        (ds.root / name).write_text(text, encoding="utf-8")


def structure_errors(ds):
    """A unit whose parent is missing, a Part or Section with no child, or no Part at all.

    Tested against every ID a filename names, so a unit with an unreadable doc,
    already reported, doesn't also make its children or parent report. A filename
    whose ID doesn't parse could be any unit's child, so then no unit reports a
    missing child.
    """
    errors = []
    parents = {uid.parent() for uid in ds.unit_ids if len(uid.levels) > 1}
    for uid, name in sorted(ds.units.items(), key=lambda kv: kv[0].levels):
        if len(uid.levels) > 1 and uid.parent() not in ds.unit_ids:
            errors.append((name, f"{uid} has no {UNIT_TYPES[len(uid.levels) - 1]} {uid.parent()}"))
        if len(uid.levels) < 3 and uid not in parents and not ds.bad_unit_id:
            errors.append((name, f"{uid} has no {UNIT_TYPES[len(uid.levels) + 1]}"))
    if not ds.bad_unit_id and not any(len(uid.levels) == 1 for uid in ds.unit_ids):
        errors.append(("index.md", "the doc set has no Part"))
    return errors


# --- check -------------------------------------------------------------------


def errors_before_derive(ds):
    """Every error check reports except edited derived content; derive runs only without them."""
    if not ds.code:
        return ds.errors
    version = format_version_errors(ds)
    if version:
        # The rest of the doc set may follow another format, which this script can't read.
        return [("index.md", e) for e in version]
    return ds.errors + structure_errors(ds) + field_errors(ds)


def check(root):
    """Every error in the doc set at root, as (filename, message)."""
    ds = load(root)
    errors = errors_before_derive(ds)
    if errors:
        return errors
    return [
        (name, "derived content differs from what derive writes; edit its source and run derive")
        for name in derived(ds)
    ]


def field_errors(ds):
    """A Field out of order, repeated, unknown to its Doc type, or required and missing."""
    errors = []
    for name, doc in ds.docs.items():
        doc_type = ds.types[name]
        if doc_type == TAGS:
            continue  # every H2 in the tags doc is a tag
        order = [n for n, _ in FIELDS[doc_type]]
        last, free, seen = -1, None, set()
        for block in doc.blocks:
            if block.name not in order:
                if doc_type in FREE_H2:
                    free = free or block.name
                else:
                    errors.append((name, f"unknown Field {block.name}"))
                continue
            i = order.index(block.name)
            if free:
                errors.append((name, f"Field {block.name} comes after free content {free}"))
            elif block.name in seen:
                errors.append((name, f"Field {block.name} appears more than once"))
            elif i < last:
                errors.append((name, f"Field {block.name} is out of order"))
            last = max(last, i)
            seen.add(block.name)
        generators = doc.field("Generators") if doc_type == SECTION else None
        if generators and not bullets_only(generators.body()):
            # Context copies the whole Field as the Section Generators, which are its bullets only.
            errors.append((name, "Field Generators holds content other than bullets"))
        for field_name, required in FIELDS[doc_type]:
            if required and field_name not in DERIVED_FIELDS and not doc.field(field_name):
                errors.append((name, f"required Field {field_name} is missing"))
    return errors


def bullets_only(body):
    """Whether every line is a top-level bullet, a line indented under one, or blank."""
    return all(re.match(r"[-+*] |[ \t]", line) or not line.strip() for line in body.split("\n"))


# --- CLI ---------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("split", help="write the doc set from a Draft")
    p.add_argument("draft_dir")
    p.add_argument("output_dir")
    p = sub.add_parser("derive", help="rewrite derived content in place")
    p.add_argument("doc_set_dir")
    p = sub.add_parser("check", help="print one line per error; exit 1 if any")
    p.add_argument("doc_set_dir")
    args = parser.parse_args(argv)

    try:
        if args.command == "split":
            split(args.draft_dir, args.output_dir)
        elif args.command == "derive":
            derive(args.doc_set_dir)
        else:
            errors = check(args.doc_set_dir)
            for name, message in errors:
                print(f"{name}: {message}")
            return 1 if errors else 0
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
