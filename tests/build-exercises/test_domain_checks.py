"""Runs each Domain reference's Exercise check, check.sh, over the fixture cases in domains/<domain>/<case>/.

The case layout and how a case passes are in docs/domain-reference.md, under "Testing a domain".
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "build-exercises" / "scripts" / "exercises.py"
SKILL_DOMAINS = REPO / "skills" / "build-exercises" / "references" / "domains"
CASES = Path(__file__).resolve().parent / "domains"
BASE_CURRICULUM = Path(__file__).resolve().parent / "fixtures" / "curriculums" / "math"  # has no Target version
ANCHOR = "MATH-01.01.01"
# The cases every domain covers, from docs/domain-reference.md.
REQUIRED_CASES = {"pass", "fail", "runtime-error", "self-check-last", "version-mismatch", "no-target-version", "env-error"}
CASE_ONLY = {"expected", "target-version"}  # files that configure a case and aren't laid over the Exercise
ELLIPSIS = "..."  # an `expected` line matching any number of printed lines, such as a tool's own error output
TIMEOUT = 300  # seconds per case, so a hanging Exercise check fails its case instead of the job


def required_domains():
    return {name.strip() for name in os.environ.get("REQUIRE_DOMAINS", "").split(",") if name.strip()}


def path_without(tool, path):
    """PATH with `tool` gone and everything else still found: each directory holding the tool is swapped for a
    directory of links to its other entries. Returns (PATH, the link directories to remove afterwards)."""
    dirs, made = [], []
    for entry in path.split(os.pathsep):
        if not entry or not (Path(entry) / tool).exists():
            dirs.append(entry)
            continue
        links = Path(tempfile.mkdtemp(prefix="path-"))
        made.append(links)
        for item in Path(entry).iterdir():
            if item.name != tool:
                (links / item.name).symlink_to(item)
        dirs.append(str(links))
    return os.pathsep.join(dirs), made


def parse_expected(text):
    """(exit code, [line patterns]) from an `expected` file."""
    first, *rest = text.split("\n")
    m = re.fullmatch(r"exit (\d+)", first)
    if not m:
        raise ValueError(f"expected's first line is {first!r}, not `exit <code>`")
    if rest and rest[-1] == "":
        rest.pop()
    return int(m.group(1)), rest


def matches(pattern, line):
    return re.fullmatch(".*".join(map(re.escape, pattern.split("*"))), line) is not None


def lines_match(patterns, lines):
    """Whether lines match patterns one for one, where a `...` pattern matches any number of lines."""
    if not patterns:
        return not lines
    if patterns[0] == ELLIPSIS:
        return any(lines_match(patterns[1:], lines[i:]) for i in range(len(lines) + 1))
    return bool(lines) and matches(patterns[0], lines[0]) and lines_match(patterns[1:], lines[1:])


class DomainChecks(unittest.TestCase):
    def test_every_domain_has_a_requires_file_and_the_cases_every_domain_covers(self):
        domains = sorted(d.name for d in SKILL_DOMAINS.iterdir() if d.is_dir())
        self.assertEqual(sorted(d.name for d in CASES.iterdir() if d.is_dir()), domains)
        for domain in domains:
            with self.subTest(domain):
                self.assertTrue((CASES / domain / "requires").is_file())
                cases = {c.name for c in (CASES / domain).iterdir() if (c / "expected").is_file()}
                self.assertLessEqual(REQUIRED_CASES, cases)

    def test_every_case_gives_its_expected_exit_code_and_lines(self):
        for domain_dir in sorted(d for d in CASES.iterdir() if d.is_dir()):
            domain = domain_dir.name
            tool = (domain_dir / "requires").read_text(encoding="utf-8").strip()
            if shutil.which(tool) is None and domain in required_domains():
                self.fail(f"{domain}: {tool} isn't on PATH, and REQUIRE_DOMAINS names {domain}")
            for case in sorted(c for c in domain_dir.iterdir() if c.is_dir()):
                with self.subTest(f"{domain}/{case.name}"):
                    if shutil.which(tool) is None:
                        self.skipTest(f"{tool} isn't on PATH")
                    self.run_case(domain, tool, case)

    def run_case(self, domain, tool, case):
        code, patterns = parse_expected((case / "expected").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            curriculum = tmp / "curriculums" / BASE_CURRICULUM.name
            shutil.copytree(BASE_CURRICULUM, curriculum)
            target = case / "target-version"
            if target.is_file():
                index = curriculum / "index.md"
                text = index.read_text(encoding="utf-8")
                field = f"## Target version\n\n{target.read_text(encoding='utf-8').strip()}\n\n## Format version"
                index.write_text(text.replace("## Format version", field, 1), encoding="utf-8")

            exercise = tmp / f"{ANCHOR}-01-{case.name}"
            filled = subprocess.run(
                [sys.executable, str(SCRIPT), "assets", domain, str(exercise), "--exercise-name", exercise.name,
                 "--curriculums", str(tmp / "curriculums")],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(filled.returncode, 0, filled.stderr)
            for path in sorted(case.rglob("*")):
                rel = path.relative_to(case)
                if path.is_file() and str(rel) not in CASE_ONLY:
                    (exercise / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, exercise / rel)

            env, made = dict(os.environ), []
            if case.name == "env-error":
                env["PATH"], made = path_without(tool, env.get("PATH", os.defpath))
            try:
                done = subprocess.run(
                    ["./check.sh"], cwd=exercise, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT,
                )
            finally:
                for links in made:
                    shutil.rmtree(links)

        report = f"expected:\n{chr(10).join(patterns)}\nprinted:\n{done.stdout}"
        self.assertEqual(done.returncode, code, report)
        self.assertTrue(lines_match(patterns, done.stdout.splitlines()), report)


if __name__ == "__main__":
    unittest.main()
