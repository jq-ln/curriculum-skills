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
a Draft, check doesn't check their Fields, and derive only links the unit IDs in
their prose.
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
    INDEX: [
        ("Intro", True),
        ("Snapshot", True),
        ("Target version", False),
        ("Format version", True),
        ("Counts", True),
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
    PART: [("Intro", True), ("Sections", True)],
    SECTION: [("Generators", True), ("Subsections", True)],
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
DERIVED_FIELDS = {"Context", "Counts", "Parts", "Sections", "Subsections"}
# Fields whose content isn't authored prose, so markers in them aren't linked: the derived ones,
# Prereqs, whose IDs derive links as entries, and Format version.
NOT_PROSE = DERIVED_FIELDS | {"Prereqs", "Format version"}
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
    return f"- {unit_link(ds, uid)}: {one_line(ds.doc(uid).field('Goal').body())}"


def link_prose(ds, name, text, errors, stale):
    """text with every own-code marker linked and every unit link refreshed.

    Appends (name, message) to errors for a malformed own-code token, an own-code ID
    naming no unit, and a link between docs that's malformed, broken or names no
    unit. A unit link with a bad target goes to stale instead: derive rewrites it.
    """

    def replace(m):
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
            words = m.group("text").split()
            uid = own_unit(ds, words[0]) if words else None
            if uid:
                if problem:
                    stale.append((name, f"{problem}; run derive to rewrite it"))
                return unit_link(ds, uid)
            errors.append((name, problem or f"link {m.group()} names no unit; write the unit's bare ID instead"))
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
    """(errors, stale) from link_prose() over every doc's authored prose, rewriting it in place."""
    errors, stale = [], []
    for name in ds.docs:
        for block in prose_blocks(ds, name):
            old = "".join(block.lines[1:])
            new = link_prose(ds, name, old, errors, stale)
            if new != old:
                block.lines[1:] = new.splitlines(keepends=True)
    return errors, stale


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


# --- derive ------------------------------------------------------------------


def derived(ds, other=lambda code: None):
    """The new text of every doc whose derived content differs from what derive writes, by filename.

    Compares parsed text before and after, so a doc derive has nothing to change
    in is left alone, whitespace and all. other(code) finds another Curriculum's
    directory for a Prereq naming it; check passes none, so a Prereq with another
    code is kept as it is and never compared.
    """
    before = {name: doc.text() for name, doc in ds.docs.items()}
    link_prose_everywhere(ds)  # first, so every copy below takes the linked text
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
            set_field(doc, SECTION, "Subsections", subsection_list(ds, split_unit_h1(doc.h1)[0]))
        elif doc_type == PART:
            set_field(doc, PART, "Sections", section_list(ds, split_unit_h1(doc.h1)[0]))
        elif doc_type == INDEX:
            set_field(doc, INDEX, "Counts", counts(ds))
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


def counts(ds):
    n = [sum(len(uid.levels) == level for uid in ds.units) for level in (1, 2, 3)]
    return f"- Parts: {n[0]}\n- Sections: {n[1]}\n- Subsections: {n[2]}"


def parts_table(ds):
    lines = ["| Part | Title | Sections | Subsections |", "| --- | --- | --- | --- |"]
    for part in sorted((u for u in ds.units if len(u.levels) == 1), key=lambda u: u.levels):
        sections = children(ds, part)
        subsections = sum(len(children(ds, s)) for s in sections)
        lines.append(f"| [{part}]({ds.units[part]}) | {ds.title(part)} | {len(sections)} | {subsections} |")
    return "\n".join(lines)


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
    for name, text in derived(ds, other_curricula(ds.root)).items():
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
    # A missing or misnamed unit already reported would also break every link and Prereq naming it.
    return errors or link_prose_everywhere(load(ds.root))[0] + prereq_errors(ds)


def check(root):
    """Every error in the doc set at root, as (filename, message)."""
    ds = load(root)
    errors = errors_before_derive(ds)
    if errors:
        return errors
    stale = link_prose_everywhere(load(root))[1]
    return stale or [
        (name, "derived content differs from what derive writes; edit its source and run derive")
        for name in derived(ds)
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
