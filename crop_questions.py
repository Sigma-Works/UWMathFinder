#!/usr/bin/env python3
"""
crop_questions.py  —  UWMathFinder question-bank builder
=========================================================

Turns your existing exam PDFs into individual cropped question images and
scaffolds entries in questions.json for the Practice Exam Generator.

WHY THIS EXISTS
---------------
The generator builds a randomized exam by stitching together individual
*questions*. Your repo only stores whole-exam PDFs, so we need to (1) cut each
exam into per-question images and (2) record which course / chapter / exam-type
each question belongs to. This script does #1 and scaffolds #2; you fill in the
classification (chapter + exam_types) — that part needs a human who knows the math.

INSTALL
-------
    pip3 install pymupdf pillow

USAGE — two modes
-----------------
1) INTERACTIVE CROP (recommended): renders each page of an exam to an image and
   lets you draw boxes around each question, saving crops automatically.

       python3 crop_questions.py crop exams/m126finalSpr2025.pdf --course "Math 126"

   For each page it opens, you type the pixel box(es). Or use the simpler
   "by-region" config below.

2) CONFIG CROP (batch / no GUI): you describe where each question is in a small
   JSON file, and the script cuts them all at once. Good for GitHub Pages workflow
   since it needs no display.

       python3 crop_questions.py batch crop_config.json

   crop_config.json looks like:
   {
     "course": "Math 126",
     "source_pdf": "exams/m126finalSpr2025.pdf",
     "answer_pdf": "exams/m126finalSpr2025Ans.pdf",
     "dpi": 150,
     "questions": [
       {
         "chapter": "taylor",
         "exam_types": ["Midterm 1", "Final"],
         "points": 10,
         "q_page": 2,  "q_box":  [40, 120, 760, 360],
         "a_page": 2,  "a_box":  [40, 120, 760, 360]
       }
     ]
   }
   Boxes are [x0, y0, x1, y1] in pixels at the chosen dpi (origin top-left).

OUTPUT
------
- PNG crops written to  questions/<id>.png  and  questions/<id>_ans.png
- Entries appended to    questions.json  (created if missing)

The generator reads questions.json directly. After running this, commit the new
PNGs in questions/ and the updated questions.json — same workflow as exams.
"""

import sys, os, json, argparse

def _need(mod):
    try:
        return __import__(mod)
    except ImportError:
        sys.exit(f"Missing dependency '{mod}'. Run:  pip3 install pymupdf pillow")

def render_page(pdf_path, page_index, dpi):
    fitz = _need("fitz")  # pymupdf imports as 'fitz'
    doc = fitz.open(pdf_path)
    if page_index < 0 or page_index >= len(doc):
        sys.exit(f"Page {page_index+1} out of range for {pdf_path} ({len(doc)} pages)")
    page = doc[page_index]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix  # has .width, .height, .save()

def crop_box(pdf_path, page_index, box, dpi, out_path):
    """Render a page then crop [x0,y0,x1,y1] px to out_path."""
    from PIL import Image
    pix = render_page(pdf_path, page_index, dpi)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    x0, y0, x1, y1 = box
    img.crop((x0, y0, x1, y1)).save(out_path)
    return out_path

def load_bank(path="questions.json"):
    if os.path.exists(path):
        return json.load(open(path))
    return []

def next_id(bank):
    n = 1
    existing = {q["id"] for q in bank}
    while f"q{n:04d}" in existing:
        n += 1
    return n

def cmd_batch(cfg_path):
    cfg = json.load(open(cfg_path))
    course      = cfg["course"]
    src_pdf     = cfg["source_pdf"]
    ans_pdf     = cfg.get("answer_pdf")
    dpi         = cfg.get("dpi", 150)
    os.makedirs("questions", exist_ok=True)
    bank = load_bank()
    n = next_id(bank)

    for q in cfg["questions"]:
        qid = f"q{n:04d}"; n += 1
        q_png = f"questions/{qid}.png"
        crop_box(src_pdf, q["q_page"]-1, q["q_box"], dpi, q_png)
        entry = {
            "id": qid,
            "course": course,
            "chapter": q["chapter"],
            "exam_types": q["exam_types"],
            "source": f"{os.path.basename(src_pdf)} (p{q['q_page']})",
            "points": q.get("points", 10),
            "image": q_png,
        }
        if ans_pdf and "a_box" in q:
            a_png = f"questions/{qid}_ans.png"
            crop_box(ans_pdf, q.get("a_page", q["q_page"])-1, q["a_box"], dpi, a_png)
            entry["answer_image"] = a_png
        bank.append(entry)
        print(f"  + {qid}  {course}/{q['chapter']}  -> {q_png}")

    json.dump(bank, open("questions.json","w"), indent=2)
    print(f"\nDone. questions.json now has {len(bank)} questions.")
    print("Commit the new questions/*.png and questions.json to your repo.")

def cmd_pages(pdf_path, dpi):
    """Utility: dump every page of a PDF to preview_pages/ so you can read off pixel boxes."""
    os.makedirs("preview_pages", exist_ok=True)
    fitz = _need("fitz")
    doc = fitz.open(pdf_path)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    for i in range(len(doc)):
        pix = render_page(pdf_path, i, dpi)
        out = f"preview_pages/{base}_p{i+1}.png"
        pix.save(out)
        print(f"  page {i+1}: {out}  ({pix.width}x{pix.height}px @ {dpi}dpi)")
    print("\nOpen these images, note the [x0,y0,x1,y1] pixel box of each question,")
    print("and put them in a crop_config.json, then run:  python3 crop_questions.py batch crop_config.json")

def main():
    ap = argparse.ArgumentParser(description="Build the UWMathFinder question bank from exam PDFs.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pages = sub.add_parser("pages", help="Render all pages of a PDF to preview_pages/ so you can read pixel coords.")
    p_pages.add_argument("pdf")
    p_pages.add_argument("--dpi", type=int, default=150)

    p_batch = sub.add_parser("batch", help="Crop questions described in a crop_config.json.")
    p_batch.add_argument("config")

    args = ap.parse_args()
    if args.cmd == "pages":
        cmd_pages(args.pdf, args.dpi)
    elif args.cmd == "batch":
        cmd_batch(args.config)

if __name__ == "__main__":
    main()
