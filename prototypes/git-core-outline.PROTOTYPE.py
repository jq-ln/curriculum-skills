"""PROTOTYPE, throwaway (wayfinder ticket #39). Maps every session of
~/Documents/curriculum/git.md into a core Part plus topic-branch Parts,
rewrites Prereqs into the new IDs, checks each Prereq points backward in
global ID order, and rolls Prereqs that leave a Part up into Part-level Needs.

Usage: python3 git-core-outline.PROTOTYPE.py ~/Documents/curriculum/git.md
"""
import re
import sys
from collections import OrderedDict

src = open(sys.argv[1]).read()

# --- old sessions: id -> (title, [prereqs]) -------------------------------
old = OrderedDict()
cur = None
for line in src.splitlines():
    m = re.match(r"^#### (\d+\.\d+) (.*)$", line)
    if m:
        cur = m.group(1)
        title = re.sub(r"\s*(`\[[^]]*\]`\s*)+$", "", m.group(2))
        old[cur] = [title, []]
        continue
    m = re.match(r"^- \*\*Prereqs:\*\* (.*)$", line)
    if m and cur:
        old[cur][1] = [p.strip() for p in m.group(1).split(",") if re.match(r"\d", p.strip())]

# --- core: authored by hand in the outline doc; here only IDs, sources, prereqs
# kind: '=' whole session, 's' shallow slice of a split session, 'n' new unit
CORE = [
    # (new id, title, kind, old id or None, [prereqs as new ids])
    ("01.01", "The model: snapshots, clones and three places", None, None, None),
    ("01.01.01", "Commits are snapshots", "=", "1.1", []),
    ("01.01.02", "Every clone is a full repository", "=", "1.2", ["01.01.01"]),
    ("01.01.03", "Working tree, index and repository", "=", "1.3", ["01.01.01"]),
    ("01.01.04", "First-time configuration", "=", "2.1", ["01.01.03"]),
    ("01.02", "Commits, branches and HEAD", None, None, None),
    ("01.02.01", "A first repository, observed", "=", "2.3", ["01.01.04"]),
    ("01.02.02", "A commit records a snapshot and its parents", "n", "3.1+3.4", ["01.02.01"]),
    ("01.02.03", "A branch is a movable name for one commit", "s", "7.1", ["01.02.02"]),
    ("01.02.04", "HEAD and detached HEAD", "=", "7.2", ["01.02.03"]),
    ("01.02.05", "A commit is on a branch when its tip reaches it", "=", "9.1", ["01.02.03"]),
    ("01.02.06", "Reading history with git log", "s", "13.1", ["01.02.05"]),
    ("01.03", "Recording changes", None, None, None),
    ("01.03.01", "The three trees and git status", "=", "11.1", ["01.01.03", "01.02.04"]),
    ("01.03.02", "Adding, removing and moving", "=", "11.2", ["01.03.01"]),
    ("01.03.03", "Ignoring files", "=", "11.3", ["01.03.02"]),
    ("01.03.04", "What git diff compares", "s", "14.1", ["01.03.01"]),
    ("01.03.05", "Committing well", "=", "11.5", ["01.03.02"]),
    ("01.04", "Branching and merging", None, None, None),
    ("01.04.01", "switch and restore vs. checkout", "=", "12.1", ["01.03.01"]),
    ("01.04.02", "What switching does to your files", "=", "16.1", ["01.04.01"]),
    ("01.04.03", "Creating, listing and deleting branches", "s", "16.2", ["01.04.02", "01.02.05"]),
    ("01.04.04", "Fast-forward and true merges", "=", "17.1", ["01.02.05", "01.04.02"]),
    ("01.04.05", "The three-way merge rule", "=", "17.2", ["01.04.04"]),
    ("01.04.06", "Resolving a conflict", "s", "17.3", ["01.04.05", "01.03.02"]),
    ("01.04.07", "Stashing work in progress", "s", "22.1+22.2", ["01.04.05", "01.03.01"]),
    ("01.05", "Undoing and recovering", None, None, None),
    ("01.05.01", "The reflog records where refs have been", "=", "8.1", ["01.02.04"]),
    ("01.05.02", "reset moves the branch", "=", "12.2", ["01.04.01", "01.05.01"]),
    ("01.05.03", "Cleaning untracked files", "=", "12.3", ["01.03.03"]),
    ("01.05.04", "Recovering a lost commit", "s", "23.1", ["01.05.01"]),
    ("01.05.05", "Synthesis: the undo table", "=", "12.4", ["01.05.02", "01.05.03", "01.05.04"]),
    ("01.06", "Working with a remote", None, None, None),
    ("01.06.01", "Remotes and remote-tracking branches", "=", "27.1", ["01.01.02", "01.02.03"]),
    ("01.06.02", "Authenticating to a host", "n", "29.1+29.2", ["01.06.01"]),
    ("01.06.03", "Fetch", "s", "28.1", ["01.06.01"]),
    ("01.06.04", "Upstream branches", "s", "16.2", ["01.06.03", "01.04.03"]),
    ("01.06.05", "Push", "=", "28.3", ["01.06.04"]),
    ("01.07", "Working on a team", None, None, None),
    ("01.07.01", "Rebase replays commits", "=", "18.1", ["01.04.05", "01.05.01"]),
    ("01.07.02", "Pull", "=", "28.2", ["01.06.04", "01.07.01", "01.04.04"]),
    ("01.07.03", "Tidying your own commits", "s", "18.3", ["01.07.01"]),
    ("01.07.04", "Rewriting shared history", "s", "18.8+28.4", ["01.07.03", "01.06.05"]),
    ("01.07.05", "Revert", "s", "19.2", ["01.04.05", "01.06.05"]),
    ("01.07.06", "Pull requests", "s", "48.1", ["01.07.02", "01.07.04"]),
    ("01.07.07", "Synthesis: merge, rebase or squash?", "=", "20.2", ["01.07.04", "01.07.05", "01.07.06"]),
]

# Old sessions wholly absorbed by the core, or whose remainder folds elsewhere
ABSORBED = {"1.1", "1.2", "1.3", "2.1", "2.3", "7.2", "8.1", "9.1", "11.1", "11.2",
            "11.3", "11.5", "12.1", "12.2", "12.3", "12.4", "16.1", "16.2", "17.1",
            "17.2", "18.1", "20.2", "27.1", "28.1", "28.2", "28.3",
            "7.1"}  # 7.1's storage claim ("a file, 41 bytes") folds into 7.5

# --- branches: (part title, [(section title, [old ids, 'd' suffix = deep remainder])])
BRANCHES = [
    ("Commands and versions", [
        ("Commands and documentation", ["2.2", "1.4"])]),
    ("Inspecting history", [
        ("Naming and selecting commits", ["10.1", "9.2", "10.2"]),
        ("git log in depth", ["13.1d", "13.3", "13.2", "13.4"]),
        ("Diff in depth", ["14.1d", "14.2", "14.3", "14.4", "14.5", "14.6"]),
        ("Paths, search and attribution", ["15.1", "15.2", "15.3", "15.4"]),
        ("Finding a regression", ["44.1", "44.2"])]),
    ("Recording and stashing in depth", [
        ("Staging and status in depth", ["11.4", "11.6"]),
        ("Stash in depth", ["22.1", "22.2d"])]),
    ("Rebasing, cherry-pick and revert", [
        ("Rebase in depth", ["18.2", "18.3d", "18.4", "18.5", "18.6", "18.7", "18.8d"]),
        ("Cherry-pick and revert", ["19.1", "19.2d", "19.4"]),
        ("Branching workflows", ["20.1"])]),
    ("The object model", [
        ("Content-addressed objects", ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6"]),
        ("Storing and naming objects", ["4.1", "4.2", "4.3"]),
        ("The hash-function transition", ["4.4"])]),
    ("The index", [
        ("The index file", ["5.1", "5.2", "5.3", "5.4"]),
        ("Commits from plumbing", ["6.1", "6.2"])]),
    ("Merging in depth", [
        ("Conflicts in depth", ["17.3d", "17.4", "17.8"]),
        ("Strategies", ["17.5", "17.6", "17.7", "17.9"])]),
    ("References", [
        ("Refs and their names", ["7.3", "7.4", "10.3", "10.4"]),
        ("Ref storage", ["7.5", "7.6", "7.7", "8.2"])]),
    ("Rewriting and recovery", [
        ("Rewriting history", ["21.1", "21.2", "21.3", "19.3"]),
        ("Recovery in depth", ["23.1d", "23.2", "23.3"])]),
    ("The repository, configuration and attributes", [
        ("Repository layout", ["24.1", "24.2", "24.3"]),
        ("Configuration", ["25.1", "25.2", "25.3"]),
        ("Attributes, filters and line endings", ["26.1", "26.2", "26.3", "26.4", "26.5"])]),
    ("Remotes in depth", [
        ("Remotes and refspecs", ["27.2", "27.3"]),
        ("Fetch and push in depth", ["28.4d", "28.5", "28.6"]),
        ("Credentials and authentication", ["29.1", "29.2"]),
        ("Hosting repositories", ["30.1", "30.2"])]),
    ("Transfer protocols", [
        ("The wire protocols", ["31.1", "31.2", "31.3", "31.4", "31.5", "31.6", "31.7", "31.8"])]),
    ("Packfiles and repository maintenance", [
        ("Packfiles", ["32.1", "32.2", "32.3", "32.4", "32.5"]),
        ("Housekeeping", ["33.1", "33.2", "33.3"]),
        ("Acceleration structures", ["9.3", "34.1", "34.2", "34.3", "34.4"])]),
    ("Partial data and large repositories", [
        ("Shallow and partial clones", ["35.1", "35.2", "35.3"]),
        ("Sparse checkout and sparse index", ["36.1", "36.2"]),
        ("Bundles", ["37.1", "37.2"]),
        ("Large-repository performance", ["38.1", "38.2", "38.3", "38.4"])]),
    ("Worktrees and submodules", [
        ("Worktrees", ["39.1", "39.2"]),
        ("Submodules and subtrees", ["40.1", "40.2", "40.3"])]),
    ("Automation: hooks, plumbing and metadata", [
        ("Hooks", ["41.1", "41.2", "41.3"]),
        ("Plumbing and scripting", ["42.1", "42.2", "42.3", "42.4"]),
        ("Notes, trailers and identities", ["43.1", "43.2"])]),
    ("Trust and security", [
        ("Tracing git itself", ["44.3"]),
        ("Signing and verification", ["45.1", "45.2", "45.3"]),
        ("Security", ["46.1", "46.2", "46.3"])]),
    ("Collaboration workflows", [
        ("The e-mail patch workflow", ["47.1", "47.2", "47.3"]),
        ("Pull-request workflows", ["48.1d", "48.2"])]),
    ("Inside git: the codebase and contributing", [
        ("Architecture of the C codebase", ["49.1", "49.2", "49.3", "49.4"]),
        ("Building and testing git", ["50.1", "50.2"]),
        ("Contributing to git", ["51.1", "51.2", "51.3"])]),
    ("Capstones", [
        ("Capstones", ["52.1", "52.2", "52.3", "52.4"])]),
]

# Where a later unit needs the deep remainder rather than the core slice
DEEP_NEEDED = {("17.4", "17.3"), ("23.2", "23.1"), ("33.1", "23.1"), ("28.6", "28.4"),
               ("19.1", "18.1")}
# Prereqs the core slice replaces: old prereq -> core unit that now carries it
CORE_FOR = {}
for nid, _t, kind, oid, _p in CORE:
    if oid:
        for o in oid.split("+"):
            CORE_FOR.setdefault(o, nid)

# --- assign new IDs ---------------------------------------------------------
new_of = {}       # old id (or old id + 'd') -> new id
rows = []         # (new id, title, origin, kind)
for pi, (ptitle, sections) in enumerate(BRANCHES, start=2):
    pid = f"{pi:02d}"
    rows.append((pid, ptitle, None, "part"))
    for si, (stitle, units) in enumerate(sections, start=1):
        sid = f"{pid}.{si:02d}"
        rows.append((sid, stitle, None, "section"))
        for ui, o in enumerate(units, start=1):
            uid = f"{sid}.{ui:02d}"
            new_of[o] = uid
            base = o.rstrip("d")
            title = old[base][0] + (" (beyond the core)" if o.endswith("d") else "")
            rows.append((uid, title, o, "unit"))

placed = {o.rstrip("d") for o in new_of} | ABSORBED
missing = [o for o in old if o not in placed and o not in CORE_FOR]
assert not missing, f"unplaced sessions: {missing}"


def resolve(unit_old, p):
    """New id for old prereq p as needed by old unit unit_old."""
    if (unit_old, p) in DEEP_NEEDED and p + "d" in new_of:
        return new_of[p + "d"]
    if p in new_of and p not in CORE_FOR:
        return new_of[p]
    if p in CORE_FOR:
        return CORE_FOR[p]
    return new_of.get(p) or new_of[p + "d"]


key = lambda i: tuple(int(x) for x in i.split("."))
prereqs = {}
for uid, title, o, kind in rows:
    if kind != "unit":
        continue
    base = o.rstrip("d")
    ps = {resolve(base, p) for p in old[base][1]}
    if o.endswith("d"):                     # a deep remainder extends its core slice
        ps.add(CORE_FOR[base])
    if base in ("3.1", "3.4"):
        ps.add("01.02.02")
    if base in ("29.1", "29.2"):
        ps.add("01.06.02")
    ps.discard(uid)
    prereqs[uid] = sorted(ps, key=key)

violations = [(u, p) for u, ps in prereqs.items() for p in ps if key(p) >= key(u)]

# --- Part-level Needs: outside prereqs rolled up to Parts ----------------------
needs = {}
for u, ps in prereqs.items():
    part = u[:2]
    for p in ps:
        if p[:2] != part:
            needs.setdefault(part, set()).add(p[:2])

# Part that no later Part needs: a leaf branch (Optional-shaped)
needed_by = {}
for part, ns in needs.items():
    for n in ns:
        needed_by.setdefault(n, set()).add(part)

# --- emit ---------------------------------------------------------------------
out = []
ptitles = {r[0]: r[1] for r in rows if r[3] == "part"}
ptitles["01"] = "Essentials"
for uid, title, o, kind in rows:
    if kind == "part":
        out.append(f"\n### GIT-{uid} {title}\n")
        ns = sorted(needs.get(uid, ()))
        out.append("Needs: " + ", ".join(f"GIT-{n} {ptitles[n]}" for n in ns))
        nb = sorted(needed_by.get(uid, ()))
        out.append("Needed by: " + (", ".join(f"GIT-{n}" for n in nb) or "nothing (leaf)"))
        out.append("")
    elif kind == "section":
        out.append(f"\n**GIT-{uid} {title}**\n")
        out.append("| ID | Title | From | Prereqs |\n| --- | --- | --- | --- |")
    else:
        src_ = f"{o.rstrip('d')}" + (" (rest)" if o.endswith("d") else "")
        out.append(f"| GIT-{uid} | {title} | {src_} | " +
                   ", ".join(f"GIT-{p}" for p in prereqs[uid]) + " |")

n_units = sum(1 for r in rows if r[3] == "unit") + sum(1 for c in CORE if c[2])
print("<!-- generated by git-core-outline.PROTOTYPE.py -->")
print(f"Units: {n_units} (core {sum(1 for c in CORE if c[2])}); "
      f"backward-Prereq violations: {len(violations)} {violations}")
print("\n".join(out))
