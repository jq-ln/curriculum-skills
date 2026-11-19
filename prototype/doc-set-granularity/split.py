# PROTOTYPE, throwaway: splits git.md into three candidate layouts for the
# "Doc set and file granularity" wayfinder ticket. Not production code.
import re, sys, os, shutil
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CODE = "GIT"
lines = SRC.read_text().splitlines()

ROMAN = {r: i for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split(), 1)}

def idx(pat):
    return next(i for i, l in enumerate(lines) if re.match(pat, l))

i_meth = idx(r"^## How the teaching methodology")
i_fields = idx(r"^## Per-session fields")
i_sources = idx(r"^## Sources")
i_outline = idx(r"^## Outline")
i_toc = idx(r"^# Table of contents")
i_notes = idx(r"^# Notes and open questions")

intro = lines[1:i_meth]
while intro and intro[-1].strip() in ("", "---"):
    intro.pop()
methodology = lines[i_meth:i_fields]
fields_tags = lines[i_fields:i_sources]
sources = lines[i_sources:i_outline]
notes = lines[i_notes:]

def fslug(t):
    t = re.sub(r"`\[[^\]]*\]`", "", t)
    t = t.replace("`", "").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t

def ghslug(t):
    t = t.lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")

# ---- parse the table of contents into Parts > Sections > Subsections
parts = []
old2new = {}
cur_part = cur_sec = cur_sub = None
for l in lines[i_toc + 1:i_notes]:
    m = re.match(r"^## Part ([IVXL]+) — (.*)$", l)
    if m:
        cur_part = {"n": ROMAN[m[1]], "title": m[2], "secs": [], "body": []}
        parts.append(cur_part); cur_sec = cur_sub = None; continue
    m = re.match(r"^### Chapter (\d+) · (.*)$", l)
    if m:
        cur_sec = {"n": len(cur_part["secs"]) + 1, "old": int(m[1]), "title": m[2], "subs": [], "body": []}
        cur_part["secs"].append(cur_sec); cur_sub = None; continue
    m = re.match(r"^#### (\d+)\.(\d+) (.*)$", l)
    if m:
        cur_sub = {"n": int(m[2]), "old": f"{m[1]}.{m[2]}", "title": m[3], "body": []}
        cur_sec["subs"].append(cur_sub)
        old2new[cur_sub["old"]] = (cur_part["n"], cur_sec["n"], cur_sub["n"])
        continue
    if cur_part: (cur_sub or cur_sec or cur_part)["body"].append(l)

def strip(b):
    b = list(b)
    while b and b[0].strip() == "": b.pop(0)
    while b and b[-1].strip() in ("", "---"): b.pop()
    return b

for p in parts:
    p["id"] = f"{CODE} {p['n']}"
    p["file"] = f"{CODE}-{p['n']}-{fslug(p['title'])}.md"
    for s in p["secs"]:
        s["id"] = f"{CODE} {p['n']}.{s['n']}"
        s["file"] = f"{CODE}-{p['n']}.{s['n']}-{fslug(s['title'])}.md"
        s["click"] = strip(s["body"])
        for u in s["subs"]:
            u["id"] = f"{CODE} {p['n']}.{s['n']}.{u['n']}"
            u["file"] = f"{CODE}-{p['n']}.{s['n']}.{u['n']}-{fslug(u['title'])}.md"
            u["heading"] = f"{u['id']} {u['title']}"
            u["anchor"] = ghslug(u["heading"])
            u["part"], u["sec"] = p, s
            u["body"] = strip(u["body"])
            s.setdefault("anchor", ghslug(f"{s['id']} {s['title']}"))

subs = {u["old"]: u for p in parts for s in p["secs"] for u in s["subs"]}
by_new = {u["id"]: u for u in subs.values()}

def prereqs_of(u):
    for l in u["body"]:
        m = re.match(r"^- \*\*Prereqs:\*\* (.*)$", l)
        if m:
            return re.findall(r"\b\d+\.\d+\b", m[1])
    return []

# ---- link targets per layout
def target(u, layout, from_file):
    if layout == "A":
        return u["file"]
    if layout == "B":
        f = u["sec"]["file"]
    else:
        f = u["part"]["file"]
    return ("" if f == from_file else f) + "#" + u["anchor"]

def render_body(u, layout, from_file):
    out = []
    for l in u["body"]:
        m = re.match(r"^- \*\*Prereqs:\*\* (.*)$", l)
        if m and prereqs_of(u):
            links = [f"[{subs[o]['id']}]({target(subs[o], layout, from_file)})" for o in prereqs_of(u)]
            l = "- **Prereqs:** " + ", ".join(links)
        out.append(l)
    return out

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")

TITLE = lines[0].lstrip("# ").replace(": Session Map", "")

def common(root, layout, unit_label):
    root.mkdir(parents=True, exist_ok=True); (root / ".marksman.toml").write_text("")
    head = [f"# {TITLE}", "", f"Curriculum code: `{CODE}`. Prototype layout {layout}: {unit_label}.", ""]
    head += [l for l in intro if not l.startswith("# ")]
    head += ["", "## Docs", "",
             f"- [Overview]({CODE}-overview.md): how the methodology shaped this Curriculum, and the ordering rationale.",
             f"- [Fields and tags]({CODE}-fields-and-tags.md): what each Field and tag means.",
             f"- [Sources]({CODE}-sources.md): the source families and link-text abbreviations.",
             f"- [Notes]({CODE}-notes.md): judgement calls, scope decisions, build notes.",
             "", "## Outline", "", "| ID | Part | Sections | Subsections |", "| --- | --- | --- | --- |"]
    for p in parts:
        n = sum(len(s["subs"]) for s in p["secs"])
        head.append(f"| {p['id']} | [{p['title']}]({p['file']}) | {len(p['secs'])} | {n} |")
    write(root / "index.md", "\n".join(head))
    write(root / f"{CODE}-overview.md", "\n".join([f"# {CODE} Overview", ""] + [re.sub(r"^#(#+)", r"\1", l) for l in methodology]))
    write(root / f"{CODE}-fields-and-tags.md", "\n".join([f"# {CODE} Fields and tags", ""] + [re.sub(r"^#(#+)", r"\1", l) for l in fields_tags]))
    write(root / f"{CODE}-sources.md", "\n".join([f"# {CODE} Sources", ""] + [re.sub(r"^#(#+)", r"\1", l) for l in sources[1:]]))
    write(root / f"{CODE}-notes.md", "\n".join([f"# {CODE} Notes", "", "> Old session numbers (such as 17.3) below are not yet rewritten to IDs.", ""] + [re.sub(r"^#", "", l) for l in notes[1:]]))

def nav(items):
    return " · ".join(f"[{t}]({f})" for t, f in items if f)

# ---------------- Layout A: one file per Subsection (plus Part and Section docs)
def layout_A(root):
    common(root, "A", "one file per Subsection, with Part and Section docs as indexes")
    flat = [u for p in parts for s in p["secs"] for u in s["subs"]]
    for p in parts:
        b = [f"# {p['id']} {p['title']}", "", nav([("Index", "index.md")]), ""] + strip(p["body"])
        for s in p["secs"]:
            b += ["", f"## [{s['id']} {s['title']}]({s['file']})", ""] + s["click"] + [""]
            b += [f"- [{u['id']} {u['title']}]({u['file']})" for u in s["subs"]]
        write(root / p["file"], "\n".join(b))
        for s in p["secs"]:
            b = [f"# {s['id']} {s['title']}", "", nav([("Index", "index.md"), (p["id"], p["file"])]), ""] + s["click"] + [""]
            for u in s["subs"]:
                goal = next((l for l in u["body"] if l.startswith("- **Goal:**")), "")
                b += [f"## [{u['heading']}]({u['file']})", "", goal.replace("- **Goal:** ", ""), ""]
            write(root / s["file"], "\n".join(b))
    for i, u in enumerate(flat):
        prev = flat[i - 1] if i else None
        nxt = flat[i + 1] if i + 1 < len(flat) else None
        b = [f"# {u['heading']}", "",
             nav([("Index", "index.md"), (u["part"]["id"], u["part"]["file"]), (u["sec"]["id"], u["sec"]["file"]),
                  ("Prev " + prev["id"] if prev else "", prev["file"] if prev else None),
                  ("Next " + nxt["id"] if nxt else "", nxt["file"] if nxt else None)]), ""]
        b += render_body(u, "A", u["file"])
        write(root / u["file"], "\n".join(b))

# ---------------- Layout B: one file per Section (Subsections as headings)
def layout_B(root):
    common(root, "B", "one file per Section; Subsections are headings inside it")
    secs = [s for p in parts for s in p["secs"]]
    for p in parts:
        b = [f"# {p['id']} {p['title']}", "", nav([("Index", "index.md")]), ""] + strip(p["body"])
        for s in p["secs"]:
            b += ["", f"## [{s['id']} {s['title']}]({s['file']})", ""] + s["click"] + [""]
            b += [f"- [{u['id']} {u['title']}]({s['file']}#{u['anchor']})" for u in s["subs"]]
        write(root / p["file"], "\n".join(b))
    for i, s in enumerate(secs):
        p = next(p for p in parts if s in p["secs"])
        prev = secs[i - 1] if i else None
        nxt = secs[i + 1] if i + 1 < len(secs) else None
        b = [f"# {s['id']} {s['title']}", "",
             nav([("Index", "index.md"), (p["id"], p["file"]),
                  ("Prev " + prev["id"] if prev else "", prev["file"] if prev else None),
                  ("Next " + nxt["id"] if nxt else "", nxt["file"] if nxt else None)]), ""] + s["click"]
        for u in s["subs"]:
            b += ["", f"## {u['heading']}", ""] + render_body(u, "B", s["file"])
        write(root / s["file"], "\n".join(b))

# ---------------- Layout C: one file per Part (Sections and Subsections as headings)
def layout_C(root):
    common(root, "C", "one file per Part; Sections and Subsections are headings inside it")
    for i, p in enumerate(parts):
        prev = parts[i - 1] if i else None
        nxt = parts[i + 1] if i + 1 < len(parts) else None
        b = [f"# {p['id']} {p['title']}", "",
             nav([("Index", "index.md"),
                  ("Prev " + prev["id"] if prev else "", prev["file"] if prev else None),
                  ("Next " + nxt["id"] if nxt else "", nxt["file"] if nxt else None)]), ""] + strip(p["body"])
        for s in p["secs"]:
            b += ["", f"## {s['id']} {s['title']}", ""] + s["click"]
            for u in s["subs"]:
                b += ["", f"### {u['heading']}", ""] + render_body(u, "C", p["file"])
        write(root / p["file"], "\n".join(b))

# ---------------- Loading cost: one Subsection plus its prereqs
def closure(old):
    seen, stack = [], [old]
    while stack:
        o = stack.pop()
        for q in prereqs_of(subs[o]):
            if q not in seen:
                seen.append(q); stack.append(q)
    return seen

def files_for(units, layout):
    if layout == "A": return sorted({u["file"] for u in units})
    if layout == "B": return sorted({u["sec"]["file"] for u in units})
    return sorted({u["part"]["file"] for u in units})

def size(root, fs):
    t = sum((root / f).read_text().count("\n") for f in fs)
    c = sum(len((root / f).read_text()) for f in fs)
    return t, c

EXAMPLES = ["17.3", "52.1"]

def loading(root, layout):
    out = [f"# How an agent loads one Subsection plus its prereqs (layout {layout})", "",
           "Token estimate: characters / 4. \"Whole files\" is what an agent gets from opening each file; \"extracted\" is what it gets if it cuts each needed Subsection out by heading.", ""]
    for ex in EXAMPLES:
        u = subs[ex]
        direct = [subs[o] for o in prereqs_of(u)]
        trans = [subs[o] for o in closure(ex)]
        out += [f"## {u['heading']}", "", f"Direct prereqs: {len(direct)}. Transitive prereqs: {len(trans)}.", ""]
        out += ["| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |", "| --- | --- | --- | --- | --- |"]
        need_text = lambda us: sum(len("\n".join(x["body"])) + len(x["heading"]) for x in us)
        for label, us in [("Unit only", [u]), ("Unit + direct prereqs", [u] + direct), ("Unit + transitive prereqs", [u] + trans)]:
            fs = files_for(us, layout)
            ln, ch = size(root, fs)
            out.append(f"| {label} | {len(fs)} | {ln} | {ch // 4:,} | {need_text(us) // 4:,} |")
        fs = files_for([u] + direct, layout)
        out += ["", "Files for unit + direct prereqs:", ""] + [f"- [{f}]({f})" for f in fs] + [""]
        if layout == "A":
            out += [f"Steps: glob `{u['file'].split('-')[0]}-{'.'.join(map(str,old2new[ex]))}-*.md` (or follow a link), read it, read each file its Prereqs line links to; recurse for transitive."]
        elif layout == "B":
            out += [f"Steps: open the Section file, find the `## {u['id']} …` heading, read to the next `## `; each prereq link is `file#anchor`, so open that file and cut at the anchor's heading."]
        else:
            out += [f"Steps: open the Part file (hundreds of lines), find the `### {u['id']} …` heading, read to the next `##`/`###`; prereq links are `file#anchor` into other Part files."]
        out.append("")
    write(root / "LOADING.md", "\n".join(out))
    return root

if OUT.exists(): shutil.rmtree(OUT)
rows = []
for L, fn, desc in [("A", layout_A, "per Subsection"), ("B", layout_B, "per Section"), ("C", layout_C, "per Part")]:
    root = OUT / f"{L}-per-{desc.split()[1].lower()}"
    fn(root)
    loading(root, L)
    files = [f for f in root.glob("*.md") if f.name != "LOADING.md"]
    n_lines = sorted(f.read_text().count("\n") for f in files if f.name.startswith(CODE + "-") and re.match(rf"{CODE}-\d", f.name))
    u = subs["17.3"]
    tr = [u] + [subs[o] for o in closure("17.3")]
    rows.append((L, desc, root.name, len(files), n_lines[len(n_lines) // 2], n_lines[-1],
                 size(root, files_for([u], L))[1] // 4, size(root, files_for(tr, L))[1] // 4, len(files_for(tr, L))))

cmp = ["# Layout comparison (PROTOTYPE, throwaway)", "",
       f"Source: `{SRC}`. {len(parts)} Parts, {sum(len(p['secs']) for p in parts)} Sections, {len(subs)} Subsections.", "",
       "Every layout is flat (one directory) and shares the same non-unit docs: `index.md`, `GIT-overview.md`, `GIT-fields-and-tags.md`, `GIT-sources.md`, `GIT-notes.md`, `.marksman.toml`. Only the unit granularity differs. Open each layout's `index.md` and `LOADING.md`.", "",
       "Example unit: GIT 7.2.3 Conflicts (was 17.3).", "",
       "| Layout | Grain | Dir | .md files | Median unit-file lines | Max unit-file lines | ~Tokens to read GIT 7.2.3 | ~Tokens with transitive prereqs (whole files) | Files for that |",
       "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for r in rows:
    cmp.append(f"| {r[0]} | {r[1]} | [{r[2]}]({r[2]}/index.md) | {r[3]} | {r[4]} | {r[5]} | {r[6]:,} | {r[7]:,} | {r[8]} |")
cmp += ["", "Known prototype gaps:", "",
        "- Only Prereqs lines are rewritten to new IDs and links. Old numbers in prose (Scope, Check, Notes) are left as-is.",
        "- In layouts B and C, version tags sit in headings, so anchors carry them (`#git-723-conflicts-stages-markers-and-styles-256-298-dev`)."]
write(OUT / "COMPARE.md", "\n".join(cmp))
print((OUT / "COMPARE.md").read_text())
