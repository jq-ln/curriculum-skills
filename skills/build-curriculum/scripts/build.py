#!/usr/bin/env python3
"""Build a Curriculum doc set from a Draft, derive its copies and check it.

Subcommands:
  split <draft-dir> <output-dir>  write the doc set from a Draft
  derive <doc-set-dir>            rewrite derived content and filenames in place
  check <doc-set-dir>             print one line per error; exit 1 if any

Follows the curriculum format in ../references/curriculum-format.md, which this
script never reads: FORMAT_VERSION and the rules below are kept in step with it,
and CI fails when FORMAT_VERSION drifts. Standard library only.
"""

import argparse
import difflib
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
    INDEX: [
        ("Intro", True),
        ("Snapshot", True),
        ("Target version", False),
        ("Format version", True),
        ("Counts", True),
        ("Docs", True),
        ("Parts", True),
    ],
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
    PART: [("Intro", True), ("Tags", False), ("Appendices", False), ("Sections", True)],
    SECTION: [("Generators", True), ("Tags", False), ("Appendices", False), ("Subsections", True)],
    SUBSECTION: [
        ("Context", True),
        ("Tags", False),
        ("Goal", True),
        ("Generators", False),
        ("Foundations", False),
        ("Scope", True),
        ("Key concepts", True),
        ("Prereqs", True),
        ("Check", True),
        ("Sources", True),
    ],
    APPENDIX: [("Purpose", True), ("Applies to", False)],
}
# H2s an Appendix can't have, though its other H2s are free content: it isn't a unit.
NOT_IN_APPENDIX = ["Tags", "Prereqs", "Check"]
# Fields derive writes. A missing one isn't a Field error: derive adds it, and check reports it
# as derived content that differs from what derive writes.
DERIVED_FIELDS = {"Context", "Counts", "Docs", "Parts", "Appendices", "Sections", "Subsections"}
# Fields whose content isn't authored prose, so markers in them aren't linked: the derived ones,
# Prereqs and Tags, whose IDs and tag names derive links as entries, Applies to, whose IDs
# stay bare, and Format version.
NOT_PROSE = DERIVED_FIELDS | {"Prereqs", "Tags", "Applies to", "Format version"}
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
# The format doc's standard tags, in its order: (name, Meaning, Where).
STANDARD_TAGS = [
    ("Synthesis", "Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own.", "doc"),
    ("Optional", "No unit outside it depends on it, so a learner may skip it.", "doc"),
]
OPTIONAL = "Optional"
WHERE = {"doc": {"doc"}, "inline": {"inline"}, "doc, inline": {"doc", "inline"}}
TAG_KEYS = ["Meaning", "Where", "Uses"]  # the bullets under a tag's heading, in order
ORIGIN_RE = re.compile(r" \((?:from \S+|inline)\)$")  # ends a Tags entry derive added
FORBIDDEN_IN_TAG = "{}[]`"
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
    m = APPENDIX_H1_RE.fullmatch(h1)
    if m:
        return APPENDIX, m.group(1), None
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

    files = draft_files(draft_dir)
    merged = {}  # filename -> (doc type, Doc)
    keys = {}  # H1 key -> filename, so a part file's unit merges into the Outline's
    code = None
    section_file = {}  # Section UnitId -> the part file holding its Subsections
    last = None  # the last Subsection read from a part file
    merges = []  # (where, code, doc type merged into, Doc), in file order
    for path, part, description in files:
        try:
            docs = split_draft(read(path))
        except BuildError as e:
            raise BuildError(f"{path.name}: {e}") from None
        for doc in docs:
            where = f"{path.name}: # {doc.h1}"
            block = MERGE_H1_RE.fullmatch(doc.h1)
            if block:
                if not part:
                    raise BuildError(f"{where}: a merge block goes at the end of a part file")
                if "".join(doc.head[1:]).strip():
                    raise BuildError(f"{where}: has content before its first Field")
                into_type = MERGE_BLOCKS[block.group(2)]
                for b in doc.blocks:
                    if b.name not in [n for n, _ in FIELDS[into_type]]:
                        raise BuildError(f"{where}: {b.name} isn't a Field of the {into_type}")
                merges.append((where, block.group(1), into_type, doc))
                continue
            if merges and merges[-1][0].startswith(f"{path.name}: "):
                raise BuildError(f"{where}: comes after a merge block, which goes at the end of a part file")
            kind = doc_type_of_h1(doc.h1)
            token = doc.h1.split(" ", 1)[0]
            if not kind and ID_RE.fullmatch(token):
                raise BuildError(f"{where}: {not_an_id(token)}")
            if not kind:
                raise BuildError(f"{where}: not the H1 of any Doc type")
            doc_type, doc_code, uid = kind
            if (doc_type == APPENDIX) != bool(description) or (description and len(docs) > 1):
                raise BuildError(f"{where}: an Appendix goes alone in its own appendix-<description>.md")
            if "".join(doc.head[1:]).strip():
                raise BuildError(f"{where}: has content before its first Field")
            if part and uid:
                if uid.levels[0] != part:
                    raise BuildError(f"{where}: isn't in {UnitId(uid.code, (part,))}, the Part this file fills")
                if len(uid.levels) == 3:
                    section = uid.parent()
                    if section_file.setdefault(section, path.name) != path.name:
                        raise BuildError(f"{where}: Section {section} is also in {section_file[section]}; a batch holds whole Sections")
                    if last and last.levels[0] == part and uid.levels < last.levels:
                        raise BuildError(f"{where}: comes after {last}; a Part's files hold its Sections in ID order")
                    last = uid
            if uid:
                errors = title_errors(split_unit_h1(doc.h1)[1])
            elif doc_type == INDEX:
                errors = title_errors(INDEX_H1_RE.fullmatch(doc.h1).group(1), "name")
            elif doc_type == APPENDIX:
                errors = title_errors(APPENDIX_H1_RE.fullmatch(doc.h1).group(2), "Appendix title")
            else:
                errors = []
            for error in errors:
                raise BuildError(f"{where}: {error}")
            if doc_type == INDEX:
                code = code or doc_code
            key = str(uid) if uid else description or doc_type
            if key not in keys:
                keys[key] = f"{doc_code}-appendix-{description}.md" if description else filename_for(doc_type, doc_code, doc.h1)
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
    for where, block_code, into_type, doc in merges:
        if block_code != code:
            raise BuildError(f"{where}: code {block_code} isn't the index's code {code}")
        h1 = f"{code} {into_type.split()[0]}"  # such as GIT Sources, for the Sources doc
        into = merged.get(filename_for(into_type, code, h1))
        if not into:
            raise BuildError(f"{where}: the Draft has no # {h1}")
        for block in doc.blocks:
            merge_field(into[1], block)
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


MERGE_H1_RE = re.compile(rf"({CODE}) (Sources added|Part notes)")
MERGE_BLOCKS = {"Sources added": SOURCES, "Part notes": NOTES}
NONE_SO_FAR = "None so far."


def table_rows(body):
    """The body rows of a body's table: (line, cells) for each row after the header and delimiter."""
    rows = [line for line in body.split("\n") if line.strip().startswith("|")][2:]
    return [(row, [cell.strip() for cell in row.strip().strip("|").split("|")]) for row in rows]


def is_bullet(line):
    return bool(re.match(r"[-+*] ", line))


def merge_field(doc, block):
    """Add a merge block Field's entries to the same Field of doc.

    A Families bullet, or an Abbreviations row with the same abbreviation and
    expansion, that doc already holds is skipped, so two batches adding one
    source write it once. An abbreviation with another expansion is added, for
    check to report.
    """
    into, added = doc.field(block.name), block.body()
    if into and into.body() not in ("", NONE_SO_FAR):
        if block.name == "Families":
            have = set(into.body().split("\n"))
            added = "\n".join(line for line in added.split("\n") if line not in have)
        elif block.name == "Abbreviations":
            have = {tuple(cells[:2]) for _, cells in table_rows(into.body())}
            added = "\n".join(line for line, cells in table_rows(added) if tuple(cells[:2]) not in have)
        if not added:
            return
        # Bullets added to bullets stay one tight list; anything else starts a new paragraph.
        tight = block.name == "Abbreviations" or (is_bullet(into.body().split("\n")[-1]) and is_bullet(added))
        joint = "\n" if tight else "\n\n"
        added = into.body() + joint + added
    if not added:
        return
    lines = [f"## {block.name}\n", "\n", added + "\n"]
    if into:
        into.lines = lines
    else:
        doc.blocks.append(Block(block.name, lines))


DRAFT_PART_RE = re.compile(r"part-([0-9]{2})(?:-([b-z]))?\.md")


DRAFT_APPENDIX_RE = re.compile(rf"appendix-({DESCRIPTION})\.md")


def draft_files(draft_dir):
    """[(path, Part number or None, Appendix description or None)] for each Draft file split reads.

    outline.md comes first, then the part files in batch order, then the Appendices.
    Raises BuildError on any other Markdown file, so a misnamed part file isn't silently skipped.
    """
    parts, appendices = [], []
    for path in sorted(draft_dir.glob("*.md")):
        part, appendix = DRAFT_PART_RE.fullmatch(path.name), DRAFT_APPENDIX_RE.fullmatch(path.name)
        if part:
            parts.append(((int(part.group(1)), part.group(2) or ""), path))
        elif appendix:
            appendices.append((path, None, appendix.group(1)))
        elif path.name != "outline.md" and not path.name.startswith("."):
            raise BuildError(f"{path.name}: isn't outline.md, part-NN.md, part-NN-<letter>.md or appendix-<description>.md")
    return [(draft_dir / "outline.md", None, None)] + [(path, key[0], None) for key, path in sorted(parts)] + appendices


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
    tags: dict = dataclass_field(default_factory=dict)  # tag name -> Tag, in the tags doc's order
    renames: dict = dataclass_field(default_factory=dict)  # filename on disk -> the filename its title gives
    errors: list = dataclass_field(default_factory=list)  # (filename, message)

    def error(self, name, message):
        self.errors.append((name, message))

    def doc(self, uid):
        return self.docs[self.units[uid]]

    def title(self, uid):
        return split_unit_h1(self.doc(uid).h1)[1]

    def uid(self, name):
        """The UnitId of the unit doc name."""
        return split_unit_h1(self.docs[name].h1)[0]

    @property
    def tags_file(self):
        return f"{self.code}-tags.md"


def load(root, renamed=False):
    """Read and classify every file in a doc set, collecting errors as it goes.

    A unit whose filename doesn't match its title is recorded in renames, and
    kept under its filename on disk, or under the one its title gives when
    renamed is true, so every link and copy derived from it names that file.
    """
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
        if uid:
            if uid in ds.units:
                ds.error(name, f"{uid} also names {ds.units[uid]}")
                ds.renames.pop(name, None)
                continue
            if renamed:
                name = ds.renames.get(name, name)
            ds.units[uid] = name
        ds.docs[name], ds.types[name] = doc, doc_type
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
    ds.tags = read_tags(ds)
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
        ds.renames[name] = unit_filename(uid, title)
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


# --- Links -------------------------------------------------------------------

# The format doc's unit marker, and an own-code token: an ID-shaped run the marker must match at its start.
MARKER_RE = re.compile(rf"\b{CODE}-[0-9]{{2}}(?:\.[0-9]{{2}}){{0,2}}(?![.-]?\w)")
# Link text with one level of nested brackets, and a destination with one level of parentheses.
LINK_TEXT = r"(?:[^\[\]\\]|\\.|\[(?:[^\[\]\\]|\\.)*\])*"
LINK_DEST = r"<[^<>\n]*>|(?:[^\s()\\]|\\.|\((?:[^\s()\\]|\\.)*\))*"
LINK_RE = re.compile(rf"!?\[({LINK_TEXT})\]\((?:{LINK_DEST})[^)]*\)")
# Inline spans in a paragraph, tried in this order at each position. Only `id` matches are
# prose; a code span, autolink, raw HTML or link (text and destination) is kept as it is.
# A shortcut reference link, `[label]` alone, can't be told from text without the
# definitions, so an ID in one is read as prose.
INLINE_RE = re.compile(
    rf"""
    (?P<code>(?P<ticks>`+).*?(?<!`)(?P=ticks)(?!`))
    | `+  # a backtick run with no closing run is literal text
    | <[A-Za-z][A-Za-z0-9+.-]{{1,31}}:[^\s<>]*>  # autolink
    | <[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+>  # email autolink
    | <!--.*?--> | </?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>  # raw HTML
    | (?P<link>(?P<bang>!?)\[(?P<text>{LINK_TEXT})\]\(\s*(?P<dest>{LINK_DEST})(?:\s+(?:"[^"]*"|'[^']*'))?\s*\))
    | !?\[{LINK_TEXT}\]\[[^\[\]]*\]  # a full or collapsed reference link
    | \\.  # an escaped character
    | (?P<tag>\{{(?P<tagname>[^{re.escape(FORBIDDEN_IN_TAG)}\n]+)\}})  # a tag marker, if it names a tag
    | (?P<id>\b[A-Z][A-Z0-9]*-[0-9][0-9.-]*\w*)
    """,
    re.S | re.X,
)
SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
LIST_ITEM_RE = re.compile(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])(?:[ \t]+|$)")
# HTML blocks of CommonMark types 6 and 7, which run to a blank line. Type 7 can't interrupt a paragraph.
HTML_BLOCK_6_RE = re.compile(
    r" {0,3}</?(?:address|article|aside|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt"
    r"|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main"
    r"|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead"
    r"|title|tr|track|ul)(?:[ \t>]|/>|$)",
    re.I,
)
HTML_BLOCK_7_RE = re.compile(r" {0,3}(?:<[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>|</[A-Za-z][A-Za-z0-9-]*\s*>)\s*$")


def strip_links(text):
    """text with every inline link replaced by its link text."""
    return LINK_RE.sub(r"\1", text)


def indent(line):
    return len(line) - len(line.lstrip(" "))


def prose_chunks(text):
    """Split a Field's content into (is_prose, text) runs, so code blocks and HTML blocks stay out.

    Each paragraph, list item and heading is its own prose run, so a code span or
    raw HTML tag can't pair across them, which CommonMark never does.

    Indented code starts after a blank line, 4 or more spaces past the indent of
    the list item it's in, if any, and runs while lines are blank or as indented.
    Tabs count as one space, as an approximation like those in scan_lines().
    """
    chunks = []  # [is_prose, text]
    fence, html_end, code_at, blank, list_indent, after_heading = None, None, None, True, 0, False
    for line in text.splitlines(keepends=True):
        prose = False
        m = FENCE_RE.match(line.lstrip(" ")) if indent(line) >= list_indent else None
        if code_at is not None and line.strip() and indent(line.expandtabs(1)) < code_at:
            code_at = None
        if html_end:
            if html_end == "blank" and not line.strip():
                html_end, prose = None, True
            elif html_end != "blank" and html_end.search(line):
                html_end = None
        elif fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line[m.end() + indent(line):].strip():
                fence = None
        elif code_at is not None:
            pass  # indented code, blank lines included
        elif blank and line.strip() and indent(line.expandtabs(1)) >= list_indent + 4:
            code_at = list_indent + 4
        elif m and not (m.group(1)[0] == "`" and "`" in line[m.end() + indent(line):]):
            fence = m.group(1)
        elif any(start.match(line) for start, _ in HTML_BLOCKS):
            start, end = next((s, e) for s, e in HTML_BLOCKS if s.match(line))
            if not end.search(line, start.match(line).end()):
                html_end = end
        elif HTML_BLOCK_6_RE.match(line) or (blank and HTML_BLOCK_7_RE.match(line)):
            html_end = "blank"
        else:
            prose = True
        if prose and line.strip():
            item = LIST_ITEM_RE.match(line)
            if item:
                list_indent = item.end()
            elif indent(line) < list_indent and blank:
                list_indent = 0  # a paragraph after the list ends it
        starts_block = prose and line.strip() and (blank or after_heading or LIST_ITEM_RE.match(line) or heading(line))
        blank, after_heading = not line.strip(), prose and bool(heading(line))
        if chunks and chunks[-1][0] == prose and not starts_block:
            chunks[-1][1] += line
        else:
            chunks.append([prose, line])
    return chunks


def own_unit(ds, word):
    """The UnitId an own-code word names, if it names a unit in the doc set."""
    uid = parse_id(word)
    return uid if uid and uid.code == ds.code and uid in ds.units else None


def unit_link(ds, uid):
    return f"[{uid} {ds.title(uid)}]({ds.units[uid]})"


def goal_entry(ds, uid):
    """A list entry linking a Subsection, with its Goal copied."""
    return f"- {unit_link(ds, uid)}: {retarget_tag_links(ds, one_line(ds.doc(uid).field('Goal').body()))}"


def retarget_tag_links(ds, text):
    """A Subsection's text to copy into another doc: each tag link to its own #tags points at the tags doc instead."""

    def replace(m):
        own = m.group("link") and not m.group("bang") and m.group("dest") == "#tags"
        return tag_link(ds, None, m.group("text")) if own and m.group("text") in ds.tags else m.group()

    return INLINE_RE.sub(replace, text)


def link_prose(ds, name, text, errors, stale, used):
    """text with every own-code and tag marker linked and every unit and tag link refreshed.

    Appends (name, message) to errors for a malformed own-code token, an own-code ID
    naming no unit, a tag whose Where lacks inline, and a link between docs that's
    malformed, broken or names no unit or tag. A unit or tag link with a bad target
    goes to stale instead: derive rewrites it. Adds each tag used to the set used.
    """

    def use_tag(tag):
        used.add(tag)
        if "inline" not in ds.tags[tag].places:
            errors.append((name, f"tag {tag} is used inline, but its Where in {ds.tags_file} lacks inline"))
        return tag_link(ds, name, tag)

    def replace(m):
        if m.group("tag"):
            if m.group("tagname") in ds.tags:
                return use_tag(m.group("tagname"))
            return "{" + INLINE_RE.sub(replace, m.group("tagname")) + "}"  # braces stay text; what's inside is prose
        if m.group("id"):
            token = m.group("id")
            if not token.startswith(f"{ds.code}-"):
                return token  # another Curriculum's code stays plain text
            marker = MARKER_RE.match(m.string, m.start())
            uid = parse_id(marker.group()) if marker else None
            if not uid:
                errors.append((name, not_an_id(token.rstrip(".-"))))
                return token
            if uid not in ds.unit_ids:
                if not ds.bad_unit_id:  # a filename whose ID doesn't parse could be this unit
                    errors.append((name, f"{uid} names no unit"))
                return token
            # Link the ID only; the rest of the token, such as a sentence's full stop, stays.
            return (unit_link(ds, uid) if uid in ds.units else marker.group()) + token[marker.end() - m.start():]
        if m.group("link") and not m.group("bang"):
            dest = m.group("dest").strip("<>")
            if SCHEME_RE.match(dest):
                return m.group()  # a link out of the Curriculum is authored
            problem = target_error(ds, name, dest)
            if m.group("text") in ds.tags:
                if problem:
                    stale.append((name, f"{problem}; run derive to rewrite it"))
                return use_tag(m.group("text"))
            words = m.group("text").split()
            uid = own_unit(ds, words[0]) if words else None
            if uid:
                if problem:
                    stale.append((name, f"{problem}; run derive to rewrite it"))
                return unit_link(ds, uid)
            errors.append((name, problem or f"link {m.group()} names no unit or tag; write the unit's bare ID or the tag's marker instead"))
        return m.group()

    return "".join(INLINE_RE.sub(replace, chunk) if prose else chunk for prose, chunk in prose_chunks(text))


def target_error(ds, name, dest):
    """Why a link target between docs is invalid, or None."""
    file, _, anchor = dest.partition("#")
    if not dest or "/" in file or "%" in dest or "\\" in dest or (not file and not anchor):
        return f"link target {dest or '(empty)'} isn't a bare sibling filename or a same-file anchor"
    target = file or name
    if target not in ds.docs:
        return f"link target {dest} names no file in the doc set"
    if anchor and anchor not in anchors(ds.docs[target]):
        return f"link target {dest} names no heading in {target}"
    return None


def anchors(doc):
    """GitHub's anchor for each heading in a doc, with -1, -2, … for repeats."""
    out, seen = set(), {}
    for _, h in scan_lines(doc.head + [line for b in doc.blocks for line in b.lines]):
        if not h:
            continue
        a = re.sub(r"[^\w\- ]", "", strip_links(h[1]).lower()).replace(" ", "-")
        n = seen.get(a, 0)
        seen[a] = n + 1
        out.add(f"{a}-{n}" if n else a)
    return out


def prose_blocks(ds, name):
    """The blocks of a doc whose content is authored prose."""
    doc = ds.docs[name]
    if ds.types[name] == TAGS:
        return doc.blocks
    return [b for b in doc.blocks if b.name not in NOT_PROSE]


def link_prose_everywhere(ds):
    """(errors, stale, used) from link_prose() over every doc's authored prose, rewriting it in place.

    used maps each filename to the set of tags its prose uses.
    """
    errors, stale, used = [], [], {}
    for name in ds.docs:
        used[name] = set()
        for block in prose_blocks(ds, name):
            old = "".join(block.lines[1:])
            new = link_prose(ds, name, old, errors, stale, used[name])
            if new != old:
                block.lines[1:] = new.splitlines(keepends=True)
    return errors, stale, used


# --- Prereqs -----------------------------------------------------------------


def entries(body):
    """A list Field's top-level bullets, each with the lines nested under it joined to it.

    None when the body holds anything else, apart from blank lines.
    """
    out = []
    for line in body.split("\n"):
        if re.match(r"[-+*] ", line):
            out.append(line[2:])
        elif line.strip() and line[0] in " \t" and out:
            out[-1] += "\n" + line
        elif line.strip():
            return None
    return out


def entry_text(entry):
    """The format doc's entry text: the first link's text when the bullet starts with a link."""
    m = INLINE_RE.match(entry)
    return m.group("text") if m and m.group("link") and not m.group("bang") else entry


def prereq_ids(ds, name):
    """[(entry, UnitId or None)] for a Subsection's Prereqs, and the errors in it."""
    doc = ds.docs[name]
    uid = split_unit_h1(doc.h1)[0]
    body = doc.field("Prereqs").body() if doc.field("Prereqs") else "None"
    if body == "None":
        return [], []
    items = entries(body)
    if items is None:
        return [], [(name, "Field Prereqs holds content other than bullets, or None alone")]
    out, errors = [], []
    for entry in items:
        text = entry_text(entry)
        word = text.split()[0] if text.split() else ""
        prereq = parse_id(word)
        if not prereq:
            errors.append((name, f"Prereqs entry `{entry}` doesn't start with an ID"))
        elif prereq.code != ds.code:
            if len(prereq.levels) != 3:
                errors.append((name, f"Prereq {prereq} isn't a Subsection ID"))
        elif entry == text and text != word:
            errors.append((name, f"Prereqs entry `{entry}` isn't an ID alone"))
        elif prereq not in ds.unit_ids or len(prereq.levels) != 3:
            if not ds.bad_unit_id:
                errors.append((name, f"Prereq {prereq} names no Subsection"))
        elif prereq.levels >= uid.levels:
            errors.append((name, f"Prereq {prereq} doesn't come before {uid}"))
        out.append((entry, prereq))
    return out, errors


def prereq_errors(ds):
    return [e for name, t in ds.types.items() if t == SUBSECTION for e in prereq_ids(ds, name)[1]]


def one_line(body):
    """A one-paragraph Field's content on one line."""
    return " ".join(line.strip() for line in body.split("\n") if line.strip())


def prereqs(ds, name, other):
    """The Prereqs Field's content. other(code) finds another Curriculum's directory, or None."""
    lines = []
    for entry, uid in prereq_ids(ds, name)[0]:
        if uid.code == ds.code:
            lines.append(goal_entry(ds, uid))
        else:
            lines.append(f"- {other_prereq(other(uid.code), uid) or entry}")
    return "\n".join(lines) or "None"


def other_prereq(root, uid):
    """`<ID> <title>: <Goal>` for a Subsection of another Curriculum, links replaced by their text, or None."""
    if root is None:
        return None
    files = list(root.glob(f"{uid}-*.md"))
    if len(files) != 1:
        return None
    try:
        doc = parse(read(files[0]))
    except (BuildError, OSError):
        return None
    unit, goal = split_unit_h1(doc.h1), doc.field("Goal")
    if not unit or unit[0] != uid or not goal or not goal.body():
        return None
    text = strip_links(one_line(goal.body()))
    return f"{uid} {unit[1]}: {text}"


def other_curricula(root):
    """A function from a code to the one directory beside root whose index.md H1 ends `(<CODE>)`."""
    found = {}

    def find(code):
        if code not in found:
            matches = []
            for d in sorted(Path(root).resolve().parent.iterdir()):
                if d == Path(root).resolve() or not (d / "index.md").is_file():
                    continue
                try:
                    m = INDEX_H1_RE.fullmatch(parse(read(d / "index.md")).h1)
                except (BuildError, OSError):
                    continue
                if m and m.group(2) == code:
                    matches.append(d)
            found[code] = matches[0] if len(matches) == 1 else None
        return found[code]

    return find


# --- Tags --------------------------------------------------------------------


@dataclass
class Tag:
    meaning: str
    where: str  # as written; WHERE maps each valid form to its places
    standard: bool = False

    @property
    def places(self):
        return WHERE.get(self.where, set())


def tag_anchor(name):
    """GitHub's heading slug for a tag name."""
    return re.sub(r"[^\w\- ]", "", name.lower()).replace(" ", "-")


def tag_link(ds, name, tag):
    """A link to a tag from the doc name: its own #tags in a Subsection, else the tag's heading in the tags doc."""
    if name and ds.types[name] == SUBSECTION:
        return f"[{tag}](#tags)"
    return f"[{tag}]({ds.tags_file}#{tag_anchor(tag)})"


def tag_bullets(block):
    """A tags doc heading's bullets as {key: value}, or None when it holds anything else."""
    items = entries(block.body())
    if items is None:
        return None
    out = {}
    for item in items:
        key, sep, value = item.partition(": ")
        if not sep or key not in TAG_KEYS or key in out or "\n" in item:
            return None
        out[key] = value
    if list(out) != [k for k in TAG_KEYS if k in out]:
        return None
    return out


def read_tags(ds):
    """Every tag a marker or Tags Field may name, standard tags first, then the tags doc's own in its order."""
    tags = {name: Tag(meaning, where, True) for name, meaning, where in STANDARD_TAGS}
    doc = ds.docs.get(ds.tags_file) if ds.code else None
    for block in doc.blocks if doc else []:
        if block.name not in tags:
            bullets = tag_bullets(block) or {}
            tags[block.name] = Tag(bullets.get("Meaning", ""), bullets.get("Where", ""))
    return tags


def tags_doc_errors(ds):
    """A tag name or anchor that breaks links, a shared anchor, and a tag's bullets out of form."""
    name = ds.tags_file
    doc = ds.docs.get(name)
    if not doc:
        return []
    errors = []
    standard = {tag for tag, _, _ in STANDARD_TAGS}
    anchors_seen = {tag_anchor(tag): f"tag {tag}" for tag in standard}
    anchors_seen.setdefault(tag_anchor(doc.h1), "the H1")
    for block in doc.blocks:
        tag = block.name
        bad = sorted(set(tag) & set(FORBIDDEN_IN_TAG))
        anchor = tag_anchor(tag)
        if bad:
            errors.append((name, f"tag {tag} contains {' '.join(bad)}, which a tag name can't"))
        elif ORIGIN_RE.search(tag):  # its own Tags entries, just the name, would read back as derived and be dropped
            errors.append((name, f"tag {tag} has a name ending in (from <ID>) or (inline), which marks a derived Tags entry"))
        elif not anchor:
            errors.append((name, f"tag {tag} has an empty anchor"))
        elif "_" in anchor or "--" in anchor or anchor[0] == "-" or anchor[-1] == "-":
            errors.append((name, f"tag {tag} has the anchor {anchor}, on which GitHub's and marksman's slugs can differ"))
        elif anchor in anchors_seen and anchors_seen[anchor] != f"tag {tag}":
            errors.append((name, f"tag {tag} has the anchor {anchor}, as {anchors_seen[anchor]} does"))
        anchors_seen.setdefault(anchor, f"tag {tag}")
        bullets = tag_bullets(block)
        if bullets is None:
            errors.append((name, f"tag {tag} holds content other than its {', '.join(TAG_KEYS)} bullets, in that order"))
        elif tag not in standard:
            if not bullets.get("Meaning"):
                errors.append((name, f"tag {tag} has no Meaning"))
            elif ORIGIN_RE.search(bullets["Meaning"]):  # its Tags entries would read back as derived and be dropped
                errors.append((name, f"tag {tag} has a Meaning ending in (from <ID>) or (inline), which marks a derived Tags entry"))
            if bullets.get("Where") not in WHERE:
                errors.append((name, f"tag {tag} has Where `{bullets.get('Where', '')}`; use doc, inline or `doc, inline`"))
    return errors


def tag_entries(ds, name):
    """(the unit's own tags its Tags Field lists, in its order, each once; the errors in it).

    An entry ending in an origin mark is one derive added, so it's left out: derive works it out again.
    """
    f = ds.docs[name].field("Tags")
    if not f:
        return [], []
    items = entries(f.body())
    if items is None:
        return [], [(name, "Field Tags holds content other than bullets")]
    out, errors = [], []
    for item in items:
        if ORIGIN_RE.search(item):
            continue
        tag = entry_text(item)
        if tag not in ds.tags:
            errors.append((name, f"Tags entry {tag} names no tag in {ds.tags_file}"))
        elif tag not in out:
            out.append(tag)
    return out, errors


def unit_names(ds, *doc_types):
    return [name for name, t in ds.types.items() if t in doc_types]


def tag_entry_errors(ds):
    return [e for name in unit_names(ds, PART, SECTION, SUBSECTION) for e in tag_entries(ds, name)[1]]


def tag_where_errors(ds):
    """An own Tags entry whose Where lacks doc."""
    errors = []
    for name in unit_names(ds, PART, SECTION, SUBSECTION):
        for tag in tag_entries(ds, name)[0]:
            if "doc" not in ds.tags[tag].places:
                errors.append((name, f"Tags entry {tag}: its Where in {ds.tags_file} lacks doc"))
    return errors


def unit_tags(ds, used):
    """Each unit's Tags entries by filename, as (tag, origin mark or ""), in tags doc order.

    A Part's and Section's are their own. A Subsection's are its own, then its Part's
    and Section's marked with that unit's ID, then those it uses inline marked inline.
    """
    own = {name: tag_entries(ds, name)[0] for name in unit_names(ds, PART, SECTION, SUBSECTION)}
    out = {}
    for name, tags in own.items():
        origins = dict.fromkeys(tags, "")
        if ds.types[name] == SUBSECTION:
            uid = ds.uid(name)
            for unit in (uid.parent().parent(), uid.parent()):  # the Part first, so it names a tag both carry
                for tag in own[ds.units[unit]]:
                    origins.setdefault(tag, f" (from {unit})")
            for tag in used[name]:
                origins.setdefault(tag, " (inline)")
        out[name] = [(tag, origins[tag]) for tag in ds.tags if tag in origins]
    return out


def optional_errors(ds):
    """A Subsection with a Prereq inside an Optional unit that the Subsection is outside."""
    own = {ds.uid(n): tag_entries(ds, n)[0] for n in unit_names(ds, PART, SECTION, SUBSECTION)}
    optional = sorted((uid for uid, tags in own.items() if OPTIONAL in tags), key=lambda u: u.levels)
    errors = []
    for name in unit_names(ds, SUBSECTION):
        uid = ds.uid(name)
        for _, prereq in prereq_ids(ds, name)[0]:
            if not prereq or prereq.code != ds.code:
                continue
            for o in optional:
                n = len(o.levels)
                if prereq.levels[:n] == o.levels and uid.levels[:n] != o.levels:
                    errors.append((name, f"Prereq {prereq} is inside Optional {o.doc_type} {o}, which no unit outside it may depend on"))
                    break
    return errors


def tags_field(ds, entries):
    return "\n".join(f"- {tag_link(ds, None, tag)}: {ds.tags[tag].meaning}{origin}" for tag, origin in entries)


def write_tags_doc(ds, uses, carried):
    """Rewrite the tags doc: the standard tags carried, then its own, each with Meaning, Where and Uses."""
    doc = ds.docs[ds.tags_file]
    blocks = []
    for tag, t in ds.tags.items():
        if t.standard and tag not in carried:
            continue
        lines = [f"## {tag}\n", "\n", f"- Meaning: {t.meaning}\n", f"- Where: {t.where}\n", f"- Uses: {uses.get(tag, 0)}\n", "\n"]
        blocks.append(Block(tag, lines))
    if blocks and doc.head[-1].strip():
        doc.head.append("\n")
    doc.blocks = blocks


# --- derive ------------------------------------------------------------------


def derived(ds, other=lambda code: None):
    """The new text of every doc whose derived content differs from what derive writes, by filename.

    Compares parsed text before and after, so a doc derive has nothing to change
    in is left alone, whitespace and all. other(code) finds another Curriculum's
    directory for a Prereq naming it; check passes none, so a Prereq with another
    code is kept as it is and never compared.
    """
    before = {name: doc.text() for name, doc in ds.docs.items()}
    used = link_prose_everywhere(ds)[2]  # first, so every copy below takes the linked text
    ds.tags = read_tags(ds)  # again, so each Meaning copied is the linked one
    tags = unit_tags(ds, used)
    uses = {}
    for name, unit in tags.items():
        if ds.types[name] == SUBSECTION:
            for tag, _ in unit:
                uses[tag] = uses.get(tag, 0) + 1
        set_field(ds.docs[name], ds.types[name], "Tags", tags_field(ds, unit) if unit else None)
    write_tags_doc(ds, uses, {tag for unit in tags.values() for tag, _ in unit})
    subsections = sorted((uid for uid in ds.units if len(uid.levels) == 3), key=lambda u: u.levels)
    for name, doc in ds.docs.items():
        doc_type = ds.types[name]
        if doc_type == SUBSECTION:
            uid = split_unit_h1(doc.h1)[0]
            i = subsections.index(uid)
            neighbours = (subsections[i - 1] if i else None, subsections[i + 1] if i + 1 < len(subsections) else None)
            doc.head[1:] = ["\n", nav(ds, uid, *neighbours) + "\n", "\n"]
            set_field(doc, SUBSECTION, "Context", context(ds, doc))
            set_field(doc, SUBSECTION, "Prereqs", prereqs(ds, name, other))
        elif doc_type == SECTION:
            set_field(doc, SECTION, "Appendices", appendix_list(ds, ds.uid(name)))
            set_field(doc, SECTION, "Subsections", subsection_list(ds, split_unit_h1(doc.h1)[0]))
        elif doc_type == PART:
            set_field(doc, PART, "Appendices", appendix_list(ds, ds.uid(name)))
            set_field(doc, PART, "Sections", section_list(ds, split_unit_h1(doc.h1)[0]))
        elif doc_type == INDEX:
            set_field(doc, INDEX, "Counts", counts(ds, uses))
            set_field(doc, INDEX, "Docs", docs_list(ds))
            set_field(doc, INDEX, "Parts", parts_table(ds))
    return {name: doc.text() for name, doc in ds.docs.items() if doc.text() != before[name]}


def children(ds, uid):
    return sorted((u for u in ds.units if u.levels[:-1] == uid.levels and len(u.levels) == len(uid.levels) + 1), key=lambda u: u.levels)


def nav(ds, uid, prev, next_):
    section, part = uid.parent(), uid.parent().parent()
    slots = ["[Index](index.md)", f"[{part}]({ds.units[part]})", f"[{section}]({ds.units[section]})"]
    if prev:
        slots.append(f"Prev [{prev}]({ds.units[prev]})")
    if next_:
        slots.append(f"Next [{next_}]({ds.units[next_]})")
    return " · ".join(slots)


def indented(body):
    """A list Field's content nested one level, as under a bullet."""
    return ["  " + line if line.strip() else line for line in body.split("\n")]


def subsection_list(ds, section):
    return "\n".join(goal_entry(ds, uid) for uid in children(ds, section))


def section_list(ds, part):
    lines = []
    for uid in children(ds, part):
        lines.append(f"- {unit_link(ds, uid)}")
        lines += indented(ds.doc(uid).field("Generators").body())
    return "\n".join(lines)


def applies_to(ds, name):
    """(the UnitIds an Appendix's Applies to names, the errors in it)."""
    f = ds.docs[name].field("Applies to")
    if not f:
        return set(), []
    items = entries(f.body())
    if items is None:
        return set(), [(name, "Field Applies to holds content other than bullets")]
    out, errors = set(), []
    for entry in items:
        uid = parse_id(entry)
        if not uid or uid.code != ds.code or len(uid.levels) == 3:
            errors.append((name, f"Applies to entry `{entry}` isn't a Part or Section ID of this Curriculum"))
        elif uid not in ds.unit_ids:
            if not ds.bad_unit_id:
                errors.append((name, f"Applies to {uid} names no {uid.doc_type}"))
        else:
            out.add(uid)
    return out, errors


def appendix_errors(ds):
    """An Appendix with an H2 only a unit has, or an Applies to naming no Part or Section."""
    errors = []
    for name in unit_names(ds, APPENDIX):
        for block in ds.docs[name].blocks:
            if block.name in NOT_IN_APPENDIX:
                errors.append((name, f"has a {block.name} Field, which an Appendix can't: it isn't a unit"))
        errors += applies_to(ds, name)[1]
    return errors


def appendix_entry(ds, name):
    doc = ds.docs[name]
    title = APPENDIX_H1_RE.fullmatch(doc.h1).group(2)
    return f"- [Appendix: {title}]({name}): {one_line(doc.field('Purpose').body())}"


def appendix_list(ds, uid):
    """The Appendices Field of the Part or Section uid: each Appendix whose Applies to names it, or None."""
    names = [name for name in sorted(unit_names(ds, APPENDIX)) if uid in applies_to(ds, name)[0]]
    return "\n".join(appendix_entry(ds, name) for name in names) or None


def docs_list(ds):
    lines = [f"- [{w}]({ds.code}-{w.lower()}.md)" for w in NAMED_TYPES]
    return "\n".join(lines + [appendix_entry(ds, name) for name in sorted(unit_names(ds, APPENDIX))])


def counts(ds, uses):
    n = [sum(len(uid.levels) == level for uid in ds.units) for level in (1, 2, 3)]
    lines = [f"- Parts: {n[0]}", f"- Sections: {n[1]}", f"- Subsections: {n[2]}"]
    return "\n".join(lines + [f"- {tag}: {uses.get(tag, 0)}" for tag, _, _ in STANDARD_TAGS])


def parts_table(ds):
    lines = ["| Part | Title | Sections | Subsections |", "| --- | --- | --- | --- |"]
    for part in sorted((u for u in ds.units if len(u.levels) == 1), key=lambda u: u.levels):
        sections = children(ds, part)
        subsections = sum(len(children(ds, s)) for s in sections)
        lines.append(f"| [{part}]({ds.units[part]}) | {ds.title(part)} | {len(sections)} | {subsections} |")
    return "\n".join(lines)


def set_field(doc, doc_type, name, body):
    """Write a Field's content, adding the Field in its place; a body of None removes it."""
    existing = doc.field(name)
    if body is None:
        if existing:
            doc.blocks.remove(existing)
        return
    lines = [f"## {name}\n", "\n"] + [line + "\n" for line in body.split("\n")] + ["\n"]
    if existing:
        existing.lines = lines
        return
    at = next(
        (i for i, b in enumerate(doc.blocks) if field_index(doc_type, b.name) > field_index(doc_type, name)),
        len(doc.blocks),
    )
    before = doc.blocks[at - 1].lines if at else doc.head
    if before[-1].strip():
        before.append("\n")  # the last block of a doc has no blank line after it
    doc.blocks.insert(at, Block(name, lines))


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
    lines += indented(ds.doc(section).field("Generators").body())
    return "\n".join(lines)


def derive(root):
    ds = load(root)
    errors = errors_before_derive(ds)
    if errors:
        raise BuildError("\n".join(f"{n}: {m}" for n, m in errors))
    if ds.renames:
        ds = load(root, renamed=True)  # so every link and copy names the new filenames
    changed = derived(ds, other_curricula(ds.root))
    for old, new in ds.renames.items():
        # Renamed, not written anew then unlinked: on a case-insensitive filesystem a
        # rename that changes only case would unlink the file just written.
        (ds.root / old).rename(ds.root / new)
    for name, text in changed.items():
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
    errors = ds.errors + structure_errors(ds) + field_errors(ds) + head_errors(ds)
    errors = errors or tags_doc_errors(ds) or tag_entry_errors(ds)
    if errors:
        # A missing or misnamed unit or tag already reported would also break every link and Prereq naming it.
        return errors
    return (
        link_prose_everywhere(load(ds.root))[0]
        + prereq_errors(ds)
        + tag_where_errors(ds)
        + optional_errors(ds)
        + abbreviation_errors(ds)
        + appendix_errors(ds)
    )


def check(root):
    """Every error in the doc set at root, as (filename, message)."""
    ds = load(root)
    renames = [(old, f"filename should be {new}, from its title; run derive to rename it") for old, new in ds.renames.items()]
    errors = errors_before_derive(ds)
    if errors:
        return renames + errors
    stale = link_prose_everywhere(load(root))[1]
    if stale:
        return renames + stale
    before = {name: doc.text() for name, doc in ds.docs.items()}
    # Diffed under the filenames on disk, so a rename alone shows only as the copies of the new title.
    return renames + [(name, message) for name in derived(ds) for message in edited_spans(ds, name, before[name])]


SPAN_LIMIT = 100  # the most characters of a span an error line quotes


def edited_spans(ds, name, old):
    """One message per span where old, a doc's text, differs word for word from its derived text.

    When the words agree, one message per place where only the whitespace differs.
    """
    doc = ds.docs[name]
    new = doc.text()
    places = locations(doc, ds.types[name])
    suffix = "; edit its source and run derive"
    old_words, new_words = list(re.finditer(r"\S+", old)), list(re.finditer(r"\S+", new))
    new_tokens = [m.group() for m in new_words]
    matcher = difflib.SequenceMatcher(None, [m.group() for m in old_words], new_tokens, autojunk=False)
    # Spans that still differ once stale copies of renamed units' titles are updated: the hand edits.
    edits = []
    if ds.renames:
        fixed = re.findall(r"\S+", retitled(ds, old))
        edits = [(j1, j2) for op, _, _, j1, j2 in difflib.SequenceMatcher(None, fixed, new_tokens, autojunk=False).get_opcodes() if op != "equal"]
    out = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            continue
        retitle = ds.renames and not any(k1 <= j2 and j1 <= k2 for k1, k2 in edits)
        end = "; run derive to copy the new title" if retitle else suffix
        where = place(places, new_words[anchor(j1, j2)].start())
        was, now = quoted(old, old_words[i1:i2]), quoted(new, new_words[j1:j2])
        if op == "replace":
            out.append(f"{where} has {was} where derive writes {now}{end}")
        elif op == "delete":
            out.append(f"{where} has {was}, which derive doesn't write{end}")
        else:
            out.append(f"{where} lacks {now}, which derive writes{end}")
    if out:
        return out
    old_lines, new_lines = old.splitlines(keepends=True), new.splitlines(keepends=True)
    starts = [0]
    for line in new_lines:
        starts.append(starts[-1] + len(line))
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    for op, _, _, j1, j2 in matcher.get_opcodes():
        if op != "equal":
            where = place(places, starts[anchor(j1, j2)])
            message = f"{where} differs in whitespace from what derive writes{suffix}"
            if message not in out:
                out.append(message)
    return out


def retitled(ds, text):
    """text with each copy of a renamed unit's old title replaced by its new one.

    A copy is a link's text or an index table cell beside the unit's filename on disk.
    Only a copy whose words give that filename counts, so a hand-edited copy stays as it is.
    """
    for old in ds.renames:
        uid = ds.uid(old)
        title, u, f = ds.title(uid), re.escape(str(uid)), re.escape(old)

        def swap(m):
            return title if unit_filename(uid, m.group()) == old else m.group()

        text = re.sub(rf"(?<=\[{u} )[^\]\n]+(?=\]\({f}\))", swap, text)
        text = re.sub(rf"(?<=\[{u}\]\({f}\) \| )[^|\n]+?(?= \|)", swap, text)
    return text


def anchor(j1, j2):
    """The index in the derived text that places a differing span j1:j2.

    A deletion is placed by the item before it, so text cut from a Field's end stays in that Field.
    """
    return j1 if j2 > j1 or not j1 else j1 - 1


def quoted(text, words):
    """The text from the first word to the last, on one line, in backticks, cut to SPAN_LIMIT characters."""
    if not words:
        return ""
    span = " ".join(text[words[0].start() : words[-1].end()].split())
    return f"`{span if len(span) <= SPAN_LIMIT else span[: SPAN_LIMIT - 1] + '…'}`"


def locations(doc, doc_type):
    """[(offset in doc.text(), what starts there)], in order: front matter, the H1, the nav line and each H2."""
    out, at = [], 0
    if doc.front:
        out.append((0, "front matter"))
        at = len("".join(doc.front))
    out.append((at, "the H1"))
    if doc_type == SUBSECTION and len(doc.head) > 1:
        out.append((at + len(doc.head[0]), "the nav line"))
    at += len("".join(doc.head))
    for block in doc.blocks:
        out.append((at, f"tag {block.name}" if doc_type == TAGS else f"Field {block.name}"))
        at += len("".join(block.lines))
    return out


def place(places, offset):
    return [what for start, what in places if start <= offset][-1]


def abbreviation_errors(ds):
    """An abbreviation in more than one row of the sources doc's Abbreviations table."""
    name = f"{ds.code}-sources.md"
    f = ds.docs[name].field("Abbreviations") if name in ds.docs else None
    expansions = {}
    for _, cells in table_rows(f.body()) if f else []:
        expansions.setdefault(cells[0], []).append(cells[1] if len(cells) > 1 else "")
    return [
        (name, f"abbreviation {abbreviation} is defined more than once, as {' and '.join(f'`{e}`' for e in found)}")
        for abbreviation, found in expansions.items()
        if len(found) > 1
    ]


def head_errors(ds):
    """A Subsection with content between its H1 and first Field other than one paragraph, the nav line.

    derive replaces that paragraph, so anything else there would be lost.
    """
    errors = []
    for name, doc in ds.docs.items():
        if ds.types[name] != SUBSECTION:
            continue
        lines = "".join(doc.head[1:]).strip("\n").split("\n")
        if lines == [""]:
            continue
        if len(lines) > 1 or not lines[0].startswith("[Index](index.md)"):  # derive always writes the nav line as one line
            errors.append((name, "has content between its H1 and first Field other than one paragraph, the nav line; move it into a Field"))
    return errors


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
            f = doc.field(field_name)
            if required and field_name not in DERIVED_FIELDS and not f:
                errors.append((name, f"required Field {field_name} is missing"))
            elif not required and field_name not in DERIVED_FIELDS and f and f.body().lower().rstrip(".") == "none":
                errors.append((name, f"Optional Field {field_name} is `{f.body()}`; leave it out when empty"))
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
