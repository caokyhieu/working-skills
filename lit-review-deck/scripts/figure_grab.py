#!/usr/bin/env python3
"""Capture a figure from a source PDF as a PNG, with provenance written beside it.

Usage:
  figure_grab.py <source.pdf> --page N --out fig.png [--rect x0,y0,x1,y1 --units frac|pt]
                 [--dpi 220] [--caption "Fig. 3: ..."] [--source-url URL] [--cite "Leis et al., SIGMOD 2026"]
  figure_grab.py <source.pdf> --probe [--pages 1-8] [--dpi 72] [--out-dir probe/]   # page images to eyeball
  figure_grab.py <source.pdf> --list-images --page N                                # embedded rasters on a page

--rect with --units frac takes fractions of the page with (0,0) at the top-left.
With --units pt it takes PDF points, also top-left origin. Without --rect the whole page
is captured. Every capture writes <out>.json: source, url, cite, page, rect, dpi, backend,
pixel size and capture date. Do not edit that file by hand; re-run the capture.

Backends, in order: PyMuPDF (pip install pymupdf), else pdftoppm (poppler-utils) with
Pillow for cropping. Never edit values, axes or labels inside a captured figure.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date


def parse_rect(text):
    parts = [float(p) for p in text.replace(" ", "").split(",")]
    if len(parts) != 4:
        sys.exit("--rect needs x0,y0,x1,y1")
    x0, y0, x1, y1 = parts
    if x1 <= x0 or y1 <= y0:
        sys.exit("--rect needs x0 < x1 and y0 < y1 (top-left origin)")
    return x0, y0, x1, y1


def have(cmd):
    return shutil.which(cmd) is not None


def import_fitz():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        pass
    try:
        import fitz                                   # pymupdf < 1.24 exposed only this name
        return fitz
    except ImportError:
        return None


# ------------------------------------------------------------------ backends
def capture_fitz(fitz, pdf, page_no, rect, units, dpi, out):
    doc = fitz.open(pdf)
    if not 1 <= page_no <= doc.page_count:
        sys.exit(f"page {page_no} out of range (1-{doc.page_count})")
    page = doc[page_no - 1]
    pw, ph = page.rect.width, page.rect.height
    clip = None
    if rect:
        x0, y0, x1, y1 = rect
        if units == "frac":
            x0, x1, y0, y1 = x0 * pw, x1 * pw, y0 * ph, y1 * ph
        clip = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    pix.save(out)
    doc.close()
    return "pymupdf", (pix.width, pix.height), (pw, ph)


def capture_poppler(pdf, page_no, rect, units, dpi, out):
    if not have("pdftoppm"):
        sys.exit("no backend: install pymupdf (pip install pymupdf) or poppler-utils (pdftoppm)")
    stem = os.path.splitext(out)[0] + "__full"
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(page_no), "-l", str(page_no),
                    "-singlefile", pdf, stem], check=True)
    full = stem + ".png"
    page_size = None
    try:
        info = subprocess.run(["pdfinfo", "-f", str(page_no), "-l", str(page_no), pdf],
                              capture_output=True, text=True, check=True).stdout
        for line in info.splitlines():
            if "page size" in line.lower():
                nums = [float(t) for t in line.replace("x", " ").split() if _isnum(t)]
                if len(nums) >= 2:
                    page_size = (nums[0], nums[1])
                break
    except Exception:
        pass
    if not rect:
        os.replace(full, out)
        return "pdftoppm", _png_size(out), page_size
    try:
        from PIL import Image
    except ImportError:
        os.replace(full, out)
        print("WARN Pillow not installed: saved the whole page, --rect ignored", file=sys.stderr)
        return "pdftoppm (uncropped)", _png_size(out), page_size
    with Image.open(full) as im:
        w, h = im.size
        x0, y0, x1, y1 = rect
        if units == "pt":
            if not page_size:
                sys.exit("--units pt needs pdfinfo for the page size; use --units frac")
            x0, x1 = x0 / page_size[0], x1 / page_size[0]
            y0, y1 = y0 / page_size[1], y1 / page_size[1]
        im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(out)
    os.remove(full)
    return "pdftoppm+pillow", _png_size(out), page_size


def _isnum(t):
    try:
        float(t)
        return True
    except ValueError:
        return False


def _png_size(path):
    import struct
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


# ------------------------------------------------------------------ helpers
def probe(pdf, pages, dpi, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    first, _, last = pages.partition("-")
    first, last = int(first), int(last or first)
    fitz = import_fitz()
    for n in range(first, last + 1):
        out = os.path.join(out_dir, f"page-{n:03d}.png")
        if fitz:
            capture_fitz(fitz, pdf, n, None, "frac", dpi, out)
        else:
            capture_poppler(pdf, n, None, "frac", dpi, out)
        print(out)
    print("\nOpen these, note the figure's fractions of the page (0,0 top-left), then re-run with "
          "--page N --rect x0,y0,x1,y1 --units frac --dpi 220")


def list_images(pdf, page_no):
    fitz = import_fitz()
    if fitz:
        doc = fitz.open(pdf)
        page = doc[page_no - 1]
        for i, info in enumerate(page.get_images(full=True), 1):
            xref = info[0]
            d = doc.extract_image(xref)
            print(f"{i}: xref={xref} {d['width']}x{d['height']} {d['ext']}")
        if not page.get_images():
            print("no embedded rasters on this page (the figure is probably vector: capture with --rect)")
        doc.close()
        return
    if have("pdfimages"):
        subprocess.run(["pdfimages", "-list", "-f", str(page_no), "-l", str(page_no), pdf], check=True)
        return
    sys.exit("needs pymupdf or poppler-utils (pdfimages)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--rect")
    ap.add_argument("--units", choices=("frac", "pt"), default="frac")
    ap.add_argument("--dpi", type=int, default=220)
    ap.add_argument("--out")
    ap.add_argument("--caption", default="")
    ap.add_argument("--cite", default="")
    ap.add_argument("--source-url", default="")
    ap.add_argument("--probe", action="store_true", help="render pages to eyeball the figure region")
    ap.add_argument("--pages", default="1-8", help="page range for --probe")
    ap.add_argument("--out-dir", default="probe", help="output directory for --probe")
    ap.add_argument("--list-images", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"no such file: {args.pdf}")
    if args.probe:
        return probe(args.pdf, args.pages, min(args.dpi, 110), args.out_dir)
    if args.list_images:
        return list_images(args.pdf, args.page)
    if not args.out:
        sys.exit("--out is required")
    if args.dpi < 150:
        print(f"WARN {args.dpi} dpi is low for a slide figure; 200-300 keeps axis labels legible",
              file=sys.stderr)

    rect = parse_rect(args.rect) if args.rect else None
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fitz = import_fitz()
    if fitz:
        backend, px, page_size = capture_fitz(fitz, args.pdf, args.page, rect, args.units, args.dpi, args.out)
    else:
        backend, px, page_size = capture_poppler(args.pdf, args.page, rect, args.units, args.dpi, args.out)

    meta = {"image": os.path.basename(args.out), "source_pdf": os.path.abspath(args.pdf),
            "source_url": args.source_url, "cite": args.cite, "caption": args.caption,
            "page": args.page, "rect": list(rect) if rect else None, "units": args.units if rect else None,
            "dpi": args.dpi, "backend": backend,
            "pixels": list(px) if px else None, "page_size_pt": list(page_size) if page_size else None,
            "captured": date.today().isoformat()}
    side = os.path.splitext(args.out)[0] + ".json"
    with open(side, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")
    print(f"{args.out}  {px[0]}x{px[1]} px via {backend}" if px else f"{args.out} via {backend}")
    print(f"{side}")
    if not (args.cite or args.source_url):
        print("WARN no --cite or --source-url: the block credit line and sources.md will be incomplete",
              file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
