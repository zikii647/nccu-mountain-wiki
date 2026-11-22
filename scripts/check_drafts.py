#!/usr/bin/env python3
"""
Node 4 Gate: Check slide drafts in slides/<topic-slug>/drafts/slide-*.md

Checks:
  (a) Slide count is between 8 and 15, filenames are sequential slide-01.md..slide-NN.md.
  (b) Every slide contains at least one wiki/ source citation, every referenced wiki/*.md
      file actually exists in the repository, and no raw/ file path is directly referenced.
  (c) PII scan (zero tolerance): Taiwan mobile numbers (09xx), landlines (excluding public
      mountain rescue hotlines), Taiwan National IDs, student IDs, license plates, bank/post
      account numbers, and personal emails.
  (d) Cross-year contradiction check: if a slide mentions contradiction keywords (矛盾/衝突/並陳),
      it must include a year/date marker (e.g., 2024, 2025, 113, 114).

Usage:
  python scripts/check_drafts.py slides/<topic-slug>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

MIN_SLIDES = 8
MAX_SLIDES = 15

# Whitelisted public emergency numbers that should NOT trigger landline/phone PII alerts
PUBLIC_HOTLINES = {
    "0800-119-119",
    "0800-018-111",
    "0800119119",
    "0800018111",
}

PII_PATTERNS = [
    ("taiwan_mobile", re.compile(r"(?<!\d)09\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)")),
    ("taiwan_landline", re.compile(r"(?<!\d)0[2-8]-\d{7,8}(?!\d)")),
    ("taiwan_national_id", re.compile(r"(?<![A-Za-z0-9])[A-Z][1289]\d{8}(?!\d)")),
    ("student_id", re.compile(r"(?<!\d)(?:10|11)\d{7}(?!\d)|114ZM1013|\b[RDBM]\d{8}\b")),
    ("license_plate", re.compile(r"(?<![A-Za-z0-9])[A-Z]{2,3}-\d{4}(?!\d)|(?<!\d)\d{3}-[A-Z]{2}(?![A-Za-z0-9])")),
    ("bank_account", re.compile(r"(?<!\d)\d{12,16}(?!\d)|(?<!\d)\d{7}-\d{7}(?!\d)")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

# Matches wiki/.../*.md in markdown links or plain text (also handles relative ../../wiki/.../*.md)
WIKI_PATH_RE = re.compile(r"(?:\.\./)*wiki/[A-Za-z0-9_./-]+\.md")
RAW_PATH_RE = re.compile(r"(?:\.\./)*raw/[^\s`)\]>\"']+")
CONTRADICTION_RE = re.compile(r"矛盾|衝突|並陳|說法不一")
DATE_MARKER_RE = re.compile(r"20\d{2}(?:[./-]\d{1,2})?|1[01]\d[./年]\d{1,2}")


def find_repo_root(start_path: Path) -> Path:
    cur = start_path.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "wiki").is_dir() and ((p / "AGENTS.md").exists() or (p / ".git").exists()):
            return p
    return Path.cwd().resolve()


def scan_pii(text: str):
    hits = []
    # Strip whitelisted public hotlines before scanning
    cleaned = text
    for hotline in PUBLIC_HOTLINES:
        cleaned = cleaned.replace(hotline, "")
    for name, pat in PII_PATTERNS:
        for m in pat.finditer(cleaned):
            hits.append((name, m.group(0)))
    return hits


def check_topic_drafts(topic_dir: Path, repo_root: Path):
    drafts_dir = topic_dir / "drafts"
    global_errors = []
    slide_results = []
    failed_slides = []

    if not drafts_dir.is_dir():
        global_errors.append(f"Missing drafts directory: {drafts_dir}")
        return {
            "passed": False,
            "topic_dir": str(topic_dir),
            "slide_count": 0,
            "global_errors": global_errors,
            "failed_slides": [],
            "slides": [],
        }

    md_files = sorted(drafts_dir.glob("*.md"))
    slide_files = [f for f in md_files if re.match(r"^slide-\d{2}\.md$", f.name)]
    unexpected_files = [f.name for f in md_files if f not in slide_files]
    if unexpected_files:
        global_errors.append(
            f"Unexpected markdown files in drafts/ (must match slide-XX.md): {unexpected_files}"
        )

    count = len(slide_files)
    if count < MIN_SLIDES or count > MAX_SLIDES:
        global_errors.append(
            f"Slide count out of range: found {count} slides, required {MIN_SLIDES}-{MAX_SLIDES}."
        )

    # Check sequential numbering 01..N
    expected_names = [f"slide-{i:02d}.md" for i in range(1, count + 1)]
    actual_names = [f.name for f in slide_files]
    if actual_names != expected_names:
        global_errors.append(
            f"Slide filenames are not sequentially numbered 01..{count:02d}: got {actual_names}"
        )

    for sf in slide_files:
        errors = []
        warnings = []
        text = sf.read_text(encoding="utf-8")

        if not text.strip():
            errors.append("Slide file is empty.")

        # Check heading
        if not re.search(r"^#\s+\S+", text, re.MULTILINE):
            errors.append("Missing top-level Markdown heading ('# Title').")

        # (b) Forbidden raw/ path references
        raw_refs = RAW_PATH_RE.findall(text)
        if raw_refs:
            errors.append(
                f"Direct raw/ path reference is forbidden (must cite wiki/ only): {sorted(set(raw_refs))}"
            )

        # (b) Wiki source citations and file existence
        raw_wiki_matches = WIKI_PATH_RE.findall(text)
        normalized_wiki = sorted({re.sub(r"^(?:\.\./)+", "", m) for m in raw_wiki_matches})
        if not normalized_wiki:
            errors.append("Missing wiki/ source citation (must include at least one 'wiki/...md' path).")
        else:
            missing_targets = []
            for wpath in normalized_wiki:
                full_target = (repo_root / wpath).resolve()
                if not full_target.is_file():
                    missing_targets.append(wpath)
            if missing_targets:
                errors.append(f"Referenced wiki/ file(s) do not exist: {missing_targets}")

        # (c) PII scan
        pii_hits = scan_pii(text)
        if pii_hits:
            formatted = [f"{kind}:'{val}'" for kind, val in pii_hits]
            errors.append(f"PII detected (must redact/remove): {', '.join(formatted)}")

        # (d) Contradiction date check
        if CONTRADICTION_RE.search(text) and not DATE_MARKER_RE.search(text):
            errors.append(
                "Cross-year/team contradiction mentioned without explicit year/date marker (e.g., 2024/2025)."
            )

        slide_ok = len(errors) == 0
        if not slide_ok:
            failed_slides.append(sf.name)

        slide_results.append({
            "file": sf.name,
            "passed": slide_ok,
            "wiki_sources": normalized_wiki,
            "errors": errors,
            "warnings": warnings,
        })

    passed = (len(global_errors) == 0) and (len(failed_slides) == 0)
    return {
        "passed": passed,
        "topic_dir": str(topic_dir),
        "slide_count": count,
        "global_errors": global_errors,
        "failed_slides": failed_slides,
        "slides": slide_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Check slide drafts (Node 4 gate).")
    parser.add_argument("topic_dir", help="Path to slides/<topic-slug> directory")
    parser.add_argument("--repo-root", default=None, help="Repository root containing wiki/")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    topic_dir = Path(args.topic_dir).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root(topic_dir)
    result = check_topic_drafts(topic_dir, repo_root)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status_str = "PASS" if result["passed"] else "FAIL"
        print("=" * 72)
        print(f"[check_drafts] STATUS: {status_str} | Slides: {result['slide_count']} (allowed {MIN_SLIDES}-{MAX_SLIDES})")
        print(f"Topic dir : {result['topic_dir']}")
        print(f"Repo root : {repo_root}")
        print("=" * 72)

        if result["global_errors"]:
            print("\nGlobal Errors:")
            for err in result["global_errors"]:
                print(f"  - [ERROR] {err}")

        print("\nPer-Slide Results:")
        for s in result["slides"]:
            tag = "PASS" if s["passed"] else "FAIL"
            src_cnt = len(s["wiki_sources"])
            print(f"  [{tag}] {s['file']} (wiki sources: {src_cnt})")
            for err in s["errors"]:
                print(f"         -> {err}")

        if result["passed"]:
            print("\nALL DRAFT CHECKS PASSED (0 PII, all wiki/ citations verified).")
            print("NEXT STEP REMINDER: 建議開一個全新對話視窗，進行獨立 AI 忠實度審查（比對 cards/ 與 drafts/），確認後再進入節點 5 渲染 deck.html。")
        else:
            print(f"\nFAILED_SLIDES: {', '.join(result['failed_slides']) if result['failed_slides'] else '(global error)'}")
            print("ACTION: 請僅退回節點 3 重修上述出錯頁面（最多 3 輪），修正後重跑本腳本。")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
