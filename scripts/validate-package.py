#!/usr/bin/env python3
"""Check Humanizer's package files without external dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "SKILL.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
PLUGIN = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def require_match(match: re.Match[str] | None, message: str) -> re.Match[str]:
    if match is None:
        raise SystemExit(message)
    return match


yaml_metadata = require_match(
    re.match(r"\A---\n(.*?)\n---\n", SKILL, re.DOTALL),
    "SKILL.md must begin with YAML metadata",
).group(1)

for unsupported_field in ("compatibility:", "allowed-tools:"):
    if re.search(rf"(?m)^{re.escape(unsupported_field)}", yaml_metadata):
        raise SystemExit(f"Remove unsupported YAML field: {unsupported_field[:-1]}")

skill_version = require_match(
    re.search(r'(?m)^\s+version:\s*["\']([^"\']+)["\']\s*$', yaml_metadata),
    "Add metadata.version to SKILL.md",
).group(1)
readme_version = require_match(
    re.search(r"(?m)^- \*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*", README),
    "Add a version entry to README.md",
).group(1)

package_versions = {skill_version, readme_version, str(PLUGIN.get("version", ""))}
if len(package_versions) != 1:
    raise SystemExit(
        f"Use one package version in all files: {sorted(package_versions)}"
    )

skill_files = {path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md")}
if SKILL_PATH.is_symlink() or skill_files != {Path("SKILL.md")}:
    raise SystemExit("Keep one regular SKILL.md at the repo root")
if PLUGIN.get("skills") != ["./"]:
    raise SystemExit("Point the Claude plugin skill loader at the repo root")

plain_language_rules = (
    "## Writing style",
    "Lead with the main point.",
    "Use common words and active voice.",
    "Keep sentences and paragraphs short.",
    "Use `must` for requirements.",
    "Keep the full technical meaning.",
)
missing_plain_language_rules = [
    rule for rule in plain_language_rules if rule not in AGENTS
]
if missing_plain_language_rules:
    raise SystemExit(
        "Add the missing Plain Language rules to AGENTS.md: "
        + ", ".join(missing_plain_language_rules)
    )

pattern_numbers = [
    int(number)
    for number in re.findall(r"(?m)^### ([0-9]+)\. ", SKILL)
]
if pattern_numbers != list(range(1, 37)):
    raise SystemExit(f"Number SKILL.md patterns from 1 through 36: {pattern_numbers}")

readme_numbers = {
    int(number) for number in re.findall(r"(?m)^\| ([0-9]+) \|", README)
}
if readme_numbers != set(range(1, 37)):
    raise SystemExit("List patterns 1 through 36 in the README table")


def section_between(text: str, start: str, end: str) -> str:
    start_at = text.find(start)
    end_at = text.find(end, start_at + len(start) if start_at != -1 else 0)
    if start_at == -1 or end_at == -1:
        raise SystemExit(f"Keep a {start} section in SKILL.md")
    return text[start_at:end_at]


def require_in(label: str, text: str, *snippets: str) -> None:
    for snippet in snippets:
        if snippet not in text:
            raise SystemExit(f"{label} must include {snippet!r}")


def quoted_after(section: str, before_marker: str) -> str:
    if before_marker not in section:
        raise SystemExit(f"Keep {before_marker} in SKILL.md")
    rest = section.split(before_marker, 1)[1]
    if "**After:**" not in rest:
        raise SystemExit(f"{before_marker} must include an After example")
    quoted: list[str] = []
    for line in rest.split("**After:**", 1)[1].splitlines():
        if line.startswith(">"):
            quoted.append(line[1:].lstrip())
            continue
        if quoted:
            break
    if not quoted:
        raise SystemExit(f"{before_marker} After must include a quoted example")
    return "\n".join(quoted)


def readme_row(number: int) -> str:
    prefix = f"| {number} |"
    for line in README.splitlines():
        if line.startswith(prefix):
            return line
    raise SystemExit(f"List pattern {number} in the README table")


section_10 = section_between(SKILL, "### 10. Forced groups of three", "### 11.")
after_10 = quoted_after(section_10, "**Before (paragraph structure):**")
require_in(
    "§10 After",
    after_10.lower(),
    "career",
    "relationship",
    "end",
    "skill",
    "these decisions rarely explain themselves.",
)
if "may take years to make sense" in after_10:
    raise SystemExit("§10 After must not replace the original lesson")

section_28 = section_between(SKILL, "### 28. Announcing the next point", "### 29.")
require_in(
    "§28",
    section_28,
    "Let's dive in",
    "this is where X becomes useful",
    "one thing that bit me",
    "Let's dive into how caching works in Next.js",
    "This is where Camus becomes useful",
)

section_31 = section_between(SKILL, "### 31. Forced punchlines and dramatic fragments", "### 32.")
if section_31.count("That is the real win.") < 2:
    raise SystemExit("§31 Before must repeat the mini-conclusion")
after_31 = quoted_after(section_31, "**Before (mini-conclusions):**")
require_in("§31 After", after_31, "Caching cuts repeat work", "Retries hide brief outages")
if "That is the real win." in after_31:
    raise SystemExit("§31 After must drop the repeated mini-conclusion")

section_36 = section_between(SKILL, "### 36. Empty credibility signals", "## Check for false positives")
after_36 = quoted_after(section_36, "**Before:**")
if "## References" not in after_36:
    raise SystemExit("§36 After must include a references section")
prose_36, references_36 = after_36.split("## References", 1)
if "Stanford Encyclopedia" in prose_36:
    raise SystemExit("§36 After must move the source out of the sentence")
require_in("§36 After", prose_36, "This tension is central to Camus's work.")
require_in("§36 After", references_36, "Stanford Encyclopedia of Philosophy")

row_9 = readme_row(9)
if "no guessing" not in row_9:
    raise SystemExit("README #9 must keep the clipped-ending example")
row_10 = readme_row(10)
if "lesson" not in row_10.lower():
    raise SystemExit("README #10 must mention the three-example lesson")
row_28 = readme_row(28)
require_in("README #28", row_28, "Let's dive in", "This is where X becomes useful")
row_31 = readme_row(31)
if "mini-conclusion" not in row_31.lower():
    raise SystemExit("README #31 must mention mini-conclusions")
row_36 = readme_row(36)
if "references" not in row_36.lower():
    raise SystemExit("README #36 must move the source to references")

if len(SKILL.splitlines()) > 500:
    raise SystemExit("Keep SKILL.md at 500 lines or fewer")

print(f"Humanizer package v{skill_version} is valid")
