"""
UW Math Exam Parser
====================
Scans all subdirectories under EXAMS_ROOT for PDFs,
parses filenames like:  m126finalWin2025.pdf
                        m126mid1Spr2024.pdf
                        m124mid2Aut2023.pdf
and writes their metadata to exams.new.json.

It does NOT touch exams.json: that file holds hand-curated topic tags and
answer-key links, so copy the new entries over yourself (see
docs/adding-an-exam.md).

Run from the repo root:
    python3 scripts/parse_exams.py

Install dependency first:
    pip3 install -r requirements.txt
"""

import os
import re
import json
import pdfplumber

# ── CONFIG ──────────────────────────────────────────────
# Path to the folder that contains all your exam PDFs
# (can be nested in subfolders — the script walks all of them)
EXAMS_ROOT = "ArchivedExams"

# Where the PDFs will live relative to index.html on your site
# e.g. "exams/m126finalWin2025.pdf"
WEB_PDF_PREFIX = "exams"

# Max characters of PDF text to store for search indexing
TEXT_PREVIEW_CHARS = 3000
# ────────────────────────────────────────────────────────


# ── FILENAME PARSER ─────────────────────────────────────
# Handles patterns like:
#   m126finalWin2025       → Math 126, Final, Winter, 2025
#   m126mid1Win2025        → Math 126, Midterm 1, Winter, 2025
#   m124mid2Aut2023        → Math 124, Midterm 2, Autumn, 2023
#   m125finalSpr2024       → Math 125, Final, Spring, 2024

COURSE_MAP = {
    "m120": "Math 120",
    "m124": "Math 124",
    "m125": "Math 125",
    "m126": "Math 126",
}

QUARTER_MAP = {
    "win": "Winter",
    "aut": "Autumn",
    "spr": "Spring",
    "sum": "Summer",
}

EXAM_TYPE_MAP = {
    "final": "Final",
    "mid1":  "Midterm 1",
    "mid2":  "Midterm 2",
    "mid3":  "Midterm 3",
}

# Regex: (course)(examtype)(quarter)(year)
# e.g.   m126    final     Win      2025
FILENAME_RE = re.compile(
    r"^(m1[2-9]\d)"           # course: m120–m129 etc.
    r"(final|mid[123])"        # exam type
    r"([A-Za-z]{3})"           # quarter abbreviation
    r"(\d{4})$",               # year
    re.IGNORECASE
)

def parse_filename(stem):
    """Parse a PDF filename stem into metadata. Returns None if unrecognized."""
    m = FILENAME_RE.match(stem)
    if not m:
        return None

    course_key  = m.group(1).lower()
    exam_key    = m.group(2).lower()
    quarter_key = m.group(3).lower()
    year        = int(m.group(4))

    course  = COURSE_MAP.get(course_key)
    exam    = EXAM_TYPE_MAP.get(exam_key)
    quarter = QUARTER_MAP.get(quarter_key)

    if not all([course, exam, quarter]):
        print(f"  ⚠️  Unrecognized token in: {stem}")
        return None

    return {
        "course":  course,
        "type":    exam,
        "quarter": quarter,
        "year":    year,
    }
# ────────────────────────────────────────────────────────


def extract_text(pdf_path):
    """Extract plain text from all pages of a PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            return " ".join(pages_text)[:TEXT_PREVIEW_CHARS]
    except Exception as e:
        print(f"  ⚠️  Could not read PDF text: {e}")
        return ""


def find_pdfs(root):
    """Walk all subdirectories and return (abs_path, filename) for every PDF."""
    results = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith(".pdf"):
                results.append((os.path.join(dirpath, fname), fname))
    return results


def main():
    if not os.path.isdir(EXAMS_ROOT):
        print(f"❌  Folder not found: '{EXAMS_ROOT}'")
        print(f"    Make sure you're running this script from inside your UWMathFinder folder.")
        return

    pdf_files = find_pdfs(EXAMS_ROOT)
    print(f"Found {len(pdf_files)} PDF(s) under '{EXAMS_ROOT}'\n")

    exams = []
    skipped = []

    for abs_path, fname in sorted(pdf_files):
        stem = os.path.splitext(fname)[0]   # strip .pdf
        print(f"Processing: {fname}")

        meta = parse_filename(stem)
        if meta is None:
            print(f"  ⚠️  Skipping — filename doesn't match expected pattern.\n")
            skipped.append(fname)
            continue

        text = extract_text(abs_path)

        exam_id = stem.lower()

        # Infer whether this is an answer key (filename ends in -key or _key or 'key')
        is_key = bool(re.search(r"[-_]?key$", stem, re.IGNORECASE))

        exams.append({
            "id":          exam_id,
            "course":      meta["course"],
            "type":        meta["type"],
            "quarter":     meta["quarter"],
            "year":        meta["year"],
            "instructor":  "Staff",           # update manually if known
            "topics":      [],                # fill in manually or with Claude
            "pdf":         f"{WEB_PDF_PREFIX}/{fname}",
            "answer_key":  "#",               # update once you have key PDFs
            "text":        text,
            "is_key":      is_key,
        })

        print(f"  ✅  {meta['course']} {meta['type']} — {meta['quarter']} {meta['year']}\n")

    # Sort by year desc, then course
    exams.sort(key=lambda e: (-e["year"], e["course"], e["type"]))

    # never overwrite the curated exams.json — write a separate file to merge from
    output_path = "exams.new.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exams, f, indent=2, ensure_ascii=False)

    print("─" * 50)
    print(f"✅  Done! Exported {len(exams)} exam(s) to '{output_path}'")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} file(s) with unrecognized names:")
        for s in skipped:
            print(f"    • {s}")
    print("\nNext step: copy the entries you need from exams.new.json into exams.json,")
    print("fill in their 'topics' (and 'answer_key'), then run:  npm run validate")


if __name__ == "__main__":
    main()
