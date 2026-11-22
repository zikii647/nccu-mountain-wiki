#!/usr/bin/env python3
"""
Node 6 Gate: Check rendered single-file HTML deck (slides/<topic-slug>/deck.html)

Checks:
  (a) HTML structure & tag integrity: <!DOCTYPE html>, balanced open/close tags,
      self-contained single-file (no external http(s) script/stylesheet links),
      keyboard navigation (ArrowLeft / ArrowRight), page counter, and safety alert CSS.
  (b) Slide count consistency: number of <section class="slide"> matches drafts/slide-*.md
      count and is between 8 and 15.
  (c) Per-slide text length & layout overflow check: visible body text chars and block
      element counts stay within single-slide limits to prevent overflow. If exceeded,
      reports exact slides so the workflow returns to Node 3 to shorten those drafts.
  (d) Final PII scan on rendered HTML visible text.

Usage:
  python scripts/check_html.py slides/<topic-slug> [--max-chars 450] [--max-total-chars 580] [--max-blocks 14]
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

MIN_SLIDES = 8
MAX_SLIDES = 15

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

BLOCK_ELEMENTS = {"h1", "h2", "h3", "h4", "p", "li", "tr", "blockquote", "pre"}

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


class DeckHTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tag_stack = []
        self.tag_errors = []
        self.external_deps = []
        self.styles = []
        self.scripts = []
        self.slides = []

        self._in_style = False
        self._in_script = False
        self._current_slide = None
        self._slide_depth = 0
        self._footer_depth = 0

    def _has_class(self, attrs_dict, target_cls: str) -> bool:
        classes = attrs_dict.get("class", "").split()
        return target_cls in classes

    def handle_starttag(self, tag, attrs):
        tag_l = tag.lower()
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}

        # Check external dependencies (must be single-file offline)
        if tag_l == "script" and re.match(r"^https?://", attrs_dict.get("src", ""), re.I):
            self.external_deps.append(f"<script src='{attrs_dict['src']}'>")
        if tag_l == "link" and re.match(r"^https?://", attrs_dict.get("href", ""), re.I):
            self.external_deps.append(f"<link href='{attrs_dict['href']}'>")

        if tag_l not in VOID_ELEMENTS:
            self.tag_stack.append((tag_l, self.getpos()))

        if tag_l == "style":
            self._in_style = True
        elif tag_l == "script":
            self._in_script = True

        # Detect slide container (<section class="slide"> or <div class="slide">)
        if self._current_slide is None and tag_l in ("section", "div") and self._has_class(attrs_dict, "slide"):
            self._current_slide = {
                "index": len(self.slides) + 1,
                "data_slide": attrs_dict.get("data-slide", f"{len(self.slides)+1:02d}"),
                "body_chunks": [],
                "footer_chunks": [],
                "block_count": 0,
                "has_alert": False,
            }
            self._slide_depth = 1
        elif self._current_slide is not None:
            if tag_l not in VOID_ELEMENTS:
                self._slide_depth += 1
            # Track source footer inside slide
            is_footer = (
                tag_l == "footer"
                or self._has_class(attrs_dict, "slide-source")
                or self._has_class(attrs_dict, "source-footer")
                or self._has_class(attrs_dict, "slide-footer")
            )
            if self._footer_depth > 0:
                if tag_l not in VOID_ELEMENTS:
                    self._footer_depth += 1
            elif is_footer:
                self._footer_depth = 1

            # Count block elements in main slide body
            if self._footer_depth == 0 and tag_l in BLOCK_ELEMENTS:
                self._current_slide["block_count"] += 1

            # Track alert styling presence
            cls_str = attrs_dict.get("class", "")
            if any(k in cls_str for k in ("alert", "warning", "caution", "callout")):
                self._current_slide["has_alert"] = True

    def handle_startendtag(self, tag, attrs):
        # Self-closing tags like <br/> or <meta/> do not push to stack
        tag_l = tag.lower()
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag_l == "link" and re.match(r"^https?://", attrs_dict.get("href", ""), re.I):
            self.external_deps.append(f"<link href='{attrs_dict['href']}'>")

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in VOID_ELEMENTS:
            return

        if tag_l == "style":
            self._in_style = False
        elif tag_l == "script":
            self._in_script = False

        if not self.tag_stack:
            self.tag_errors.append(f"Unexpected closing tag </{tag_l}> at line {self.getpos()[0]}.")
        else:
            top_tag, top_pos = self.tag_stack[-1]
            if top_tag == tag_l:
                self.tag_stack.pop()
            else:
                # Attempt recovery if matching tag exists deeper in stack
                found_idx = None
                for idx in range(len(self.tag_stack) - 1, -1, -1):
                    if self.tag_stack[idx][0] == tag_l:
                        found_idx = idx
                        break
                if found_idx is not None:
                    unclosed = self.tag_stack[found_idx + 1:]
                    for ut, upos in unclosed:
                        self.tag_errors.append(
                            f"Unclosed tag <{ut}> opened at line {upos[0]} (encountered </{tag_l}> at line {self.getpos()[0]})."
                        )
                    self.tag_stack = self.tag_stack[:found_idx]
                else:
                    self.tag_errors.append(
                        f"Mismatched closing tag </{tag_l}> at line {self.getpos()[0]} (expected </{top_tag}> from line {top_pos[0]})."
                    )

        if self._current_slide is not None:
            if self._footer_depth > 0:
                self._footer_depth -= 1
            self._slide_depth -= 1
            if self._slide_depth == 0:
                self.slides.append(self._current_slide)
                self._current_slide = None

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
            return
        if self._in_script:
            self.scripts.append(data)
            return
        if self._current_slide is not None:
            if self._footer_depth > 0:
                self._current_slide["footer_chunks"].append(data)
            else:
                self._current_slide["body_chunks"].append(data)

    def finalize(self):
        for ut, upos in reversed(self.tag_stack):
            self.tag_errors.append(f"Unclosed tag <{ut}> opened at line {upos[0]}.")


def visible_char_count(chunks) -> int:
    text = "".join(chunks)
    # Collapse whitespace and count non-whitespace characters for accurate CJK + Latin density
    compact = re.sub(r"\s+", "", text)
    return len(compact)


def scan_pii(text: str):
    hits = []
    cleaned = text
    for hotline in PUBLIC_HOTLINES:
        cleaned = cleaned.replace(hotline, "")
    for name, pat in PII_PATTERNS:
        for m in pat.finditer(cleaned):
            hits.append((name, m.group(0)))
    return hits


def check_html(topic_dir: Path, max_chars: int, max_total_chars: int, max_blocks: int):
    deck_path = topic_dir / "deck.html"
    drafts_dir = topic_dir / "drafts"
    global_errors = []
    overflow_slides = []
    slide_reports = []

    if not deck_path.is_file():
        return {
            "passed": False,
            "deck_path": str(deck_path),
            "html_slide_count": 0,
            "draft_slide_count": 0,
            "global_errors": [f"Missing deck.html at {deck_path}"],
            "overflow_slides": [],
            "slides": [],
        }

    html_text = deck_path.read_text(encoding="utf-8")

    # Basic document markers
    if not re.search(r"<!DOCTYPE\s+html>", html_text, re.I):
        global_errors.append("Missing <!DOCTYPE html> declaration.")
    for req_tag in ("<html", "<head", "<body"):
        if req_tag not in html_text.lower():
            global_errors.append(f"Missing required {req_tag}> element.")

    validator = DeckHTMLValidator()
    validator.feed(html_text)
    validator.close()
    validator.finalize()

    if validator.tag_errors:
        global_errors.extend(validator.tag_errors[:10])
        if len(validator.tag_errors) > 10:
            global_errors.append(f"... and {len(validator.tag_errors) - 10} more HTML tag errors.")

    if validator.external_deps:
        global_errors.append(
            f"External CDN dependencies found (must be single-file offline HTML): {validator.external_deps}"
        )

    all_js = "\n".join(validator.scripts)
    all_css = "\n".join(validator.styles)

    # Check keyboard navigation
    if "ArrowRight" not in all_js or "ArrowLeft" not in all_js:
        global_errors.append("Missing keyboard navigation ('ArrowLeft' / 'ArrowRight') in inline <script>.")

    # Check page counter logic or markup
    has_counter = bool(
        re.search(r"page-?num|slide-?counter|slide-?num|currentSlide|totalSlides", html_text, re.I)
    )
    if not has_counter:
        global_errors.append("Missing page number / slide counter markup or logic.")

    # Check safety alert CSS styles
    has_alert_css = bool(
        re.search(r"\.(?:alert|warning|caution|callout|safety-alert|safety-warning)", all_css, re.I)
    )
    if not has_alert_css:
        global_errors.append("Missing safety alert CSS classes (e.g., .alert-warning / .callout) in inline <style>.")

    # Slide count vs drafts count
    draft_files = sorted(drafts_dir.glob("slide-[0-9][0-9].md")) if drafts_dir.is_dir() else []
    draft_count = len(draft_files)
    html_count = len(validator.slides)

    if html_count < MIN_SLIDES or html_count > MAX_SLIDES:
        global_errors.append(
            f"HTML slide count out of range: found {html_count}, required {MIN_SLIDES}-{MAX_SLIDES}."
        )
    if draft_count > 0 and html_count != draft_count:
        global_errors.append(
            f"HTML slide count ({html_count}) does not match drafts/ count ({draft_count})."
        )

    # Per-slide text overflow & PII scan
    for s in validator.slides:
        body_chars = visible_char_count(s["body_chunks"])
        footer_chars = visible_char_count(s["footer_chunks"])
        total_chars = body_chars + footer_chars
        blocks = s["block_count"]
        slide_id = f"slide-{int(s['index']):02d}.md"
        slide_errors = []

        if body_chars == 0:
            slide_errors.append("Slide body has 0 visible characters.")
        if body_chars > max_chars:
            slide_errors.append(
                f"Body text overflow: {body_chars} chars > limit {max_chars} (shorten draft in Node 3, do not cram!)."
            )
        if total_chars > max_total_chars:
            slide_errors.append(
                f"Total slide text overflow: {total_chars} chars > limit {max_total_chars}."
            )
        if blocks > max_blocks:
            slide_errors.append(
                f"Too many content blocks/items: {blocks} blocks > limit {max_blocks} (risk of vertical overflow)."
            )

        slide_raw_text = " ".join(s["body_chunks"] + s["footer_chunks"])
        pii_hits = scan_pii(slide_raw_text)
        if pii_hits:
            formatted = [f"{k}:'{v}'" for k, v in pii_hits]
            slide_errors.append(f"PII detected in rendered slide: {', '.join(formatted)}")

        if slide_errors:
            overflow_slides.append(slide_id)

        slide_reports.append({
            "slide": slide_id,
            "data_slide": s["data_slide"],
            "body_chars": body_chars,
            "footer_chars": footer_chars,
            "total_chars": total_chars,
            "blocks": blocks,
            "passed": len(slide_errors) == 0,
            "errors": slide_errors,
        })

    passed = (len(global_errors) == 0) and (len(overflow_slides) == 0)
    return {
        "passed": passed,
        "deck_path": str(deck_path),
        "html_slide_count": html_count,
        "draft_slide_count": draft_count,
        "limits": {
            "max_chars": max_chars,
            "max_total_chars": max_total_chars,
            "max_blocks": max_blocks,
        },
        "global_errors": global_errors,
        "overflow_slides": overflow_slides,
        "slides": slide_reports,
    }


def main():
    parser = argparse.ArgumentParser(description="Check rendered deck.html (Node 6 gate).")
    parser.add_argument("topic_dir", help="Path to slides/<topic-slug> directory")
    parser.add_argument("--max-chars", type=int, default=450, help="Max non-whitespace body chars per slide (default: 450)")
    parser.add_argument("--max-total-chars", type=int, default=580, help="Max total non-whitespace chars per slide incl. source footer (default: 580)")
    parser.add_argument("--max-blocks", type=int, default=14, help="Max block elements (p/li/tr/headings) per slide (default: 14)")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    topic_dir = Path(args.topic_dir).resolve()
    result = check_html(topic_dir, args.max_chars, args.max_total_chars, args.max_blocks)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status_str = "PASS" if result["passed"] else "FAIL"
        print("=" * 76)
        print(
            f"[check_html] STATUS: {status_str} | HTML slides: {result['html_slide_count']} "
            f"| Drafts: {result['draft_slide_count']} | Limits: body<={args.max_chars}c, blocks<={args.max_blocks}"
        )
        print(f"Deck path: {result['deck_path']}")
        print("=" * 76)

        if result["global_errors"]:
            print("\nGlobal / Structure Errors:")
            for err in result["global_errors"]:
                print(f"  - [ERROR] {err}")

        if result["slides"]:
            print("\nPer-Slide Density & Overflow Report:")
            print(f"  {'Slide':<14} {'Body':>6} {'Total':>6} {'Blocks':>7}  Status")
            print("  " + "-" * 48)
            for s in result["slides"]:
                tag = "PASS" if s["passed"] else "FAIL"
                print(
                    f"  {s['slide']:<14} {s['body_chars']:>6} {s['total_chars']:>6} {s['blocks']:>7}  [{tag}]"
                )
                for err in s["errors"]:
                    print(f"      -> {err}")

        if result["passed"]:
            print("\nALL HTML CHECKS PASSED. Ready to generate report.md!")
        else:
            if result["overflow_slides"]:
                print(f"\nOVERFLOW_OR_FAILED_SLIDES: {', '.join(result['overflow_slides'])}")
                print("ACTION: 請退回節點 3 縮短上述頁面逐頁稿（禁止硬塞版面），再經節點 4、5、6 重驗。")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
