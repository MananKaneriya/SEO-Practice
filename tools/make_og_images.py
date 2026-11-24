"""Generate the social-share (Open Graph) images and the logo for the site.

Run from anywhere:   python tools/make_og_images.py
Needs Pillow:        pip install Pillow

For every index.html it reads the og:image URL and the og:title, then draws a 1200x630 JPG:
dark background, "Ortheon AI" small at the top, the page's og:title in large white text,
centred. The script checks that no line of text is cut off or touches the edge.
Output: real baseline JPEG, RGB, quality 88 (each file is far below the 300 KB limit).
Also writes images/logo.png (512x512). Old JPGs in images/og/ are removed first, so the
folder always matches the pages exactly.
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = "Ortheon AI"
W, H = 1200, 630
BG, ACCENT, WHITE, MUTED, LIGHT_BLUE = (15, 23, 42), (37, 99, 235), (255, 255, 255), (148, 163, 184), (96, 165, 250)
MAX_TEXT_WIDTH = 1000      # the title never gets wider than this (100 px of margin each side)
TEXT_AREA = (140, 590)     # the title is centred vertically inside this band, below the brand line
MAX_LINES = 3

# first bold font that exists on this computer (Windows, macOS, Linux)
BOLD = next((f for f in (
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
) if Path(f).is_file()), None)
if BOLD is None:
    sys.exit("No usable TrueType font found. Edit the font list in tools/make_og_images.py.")


def font(size):
    return ImageFont.truetype(BOLD, size)


def wrap(draw, text, fnt, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            # don't strand a tiny word ("in", "&") at the end of a line: carry it to the next line
            parts = current.split(" ")
            if len(parts) > 1 and len(parts[-1]) <= 2:
                lines.append(" ".join(parts[:-1]))
                current = f"{parts[-1]} {word}"
            else:
                lines.append(current)
                current = word
    lines.append(current)
    return lines


def og_image(out, title):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, H], fill=ACCENT)                                   # accent bar, left edge

    brand_font = font(34)                                                     # brand: small, centred, at the top
    d.text(((W - d.textlength(BRAND, font=brand_font)) / 2, 56), BRAND, font=brand_font, fill=MUTED)

    size = 112
    while True:                                                               # largest size that fits
        fnt = font(size)
        lines = wrap(d, title, fnt, MAX_TEXT_WIDTH)
        widest = max(d.textlength(line, font=fnt) for line in lines)
        line_h = int(size * 1.22)
        if (len(lines) <= MAX_LINES and widest <= MAX_TEXT_WIDTH and len(lines) * line_h <= TEXT_AREA[1] - TEXT_AREA[0]) or size <= 40:
            break
        size -= 4

    top = TEXT_AREA[0] + ((TEXT_AREA[1] - TEXT_AREA[0]) - len(lines) * line_h) / 2
    for i, line in enumerate(lines):
        x = (W - d.textlength(line, font=fnt)) / 2
        y = top + i * line_h
        d.text((x, y), line, font=fnt, fill=WHITE)
        left, _, right, bottom = d.textbbox((x, y), line, font=fnt)
        # nothing may be cut off or touch the edge
        assert left >= 60 and right <= W - 60 and bottom <= H - 30, f"text would be cut off: {title!r} ({left},{right},{bottom})"
    img.save(out, "JPEG", quality=88, optimize=True)
    return size, len(lines)


def logo(out):
    img = Image.new("RGB", (512, 512), BG)
    d = ImageDraw.Draw(img)
    fnt = font(112)
    first, second = BRAND.split(" ", 1)
    for text, y, colour in ((first, 140, WHITE), (second, 252, LIGHT_BLUE)):
        d.text(((512 - d.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=colour)
    d.rectangle([196, 400, 316, 408], fill=ACCENT)
    img.save(out, "PNG", optimize=True)


def main():
    og_dir = ROOT / "images" / "og"
    og_dir.mkdir(parents=True, exist_ok=True)
    for old in og_dir.glob("*.jpg"):
        old.unlink()

    pages = [p for p in sorted(ROOT.rglob("index.html")) if ".git" not in p.parts]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        img_url = re.search(r'<meta property="og:image" content="([^"]+)"', text).group(1)
        title = html.unescape(re.search(r'<meta property="og:title" content="([^"]+)"', text).group(1))
        out = ROOT / urlparse(img_url).path.lstrip("/")
        size, n_lines = og_image(out, title)
        print(f"{out.stat().st_size // 1024:4d} KB  {size:3d}px x{n_lines}  {out.relative_to(ROOT).as_posix():58} {title}")

    logo(ROOT / "images" / "logo.png")
    print("      images/logo.png")


if __name__ == "__main__":
    main()
