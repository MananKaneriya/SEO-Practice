"""Generate the social-share (Open Graph) images and the logo for the site.

Run from anywhere:   python tools/make_og_images.py
Needs Pillow:        pip install Pillow

For every index.html it reads the og:image URL and the <h1>, then draws a 1200x630 JPG:
dark background, "Ortheon AI" small at the top, the page's H1 in large white text.
Also writes images/logo.png (512x512). Old JPGs in images/og/ are removed first, so the
folder always matches the pages exactly. Each JPG stays far below the 300 KB limit.
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = "Ortheon AI"
BG, ACCENT, WHITE, MUTED, LIGHT_BLUE = (15, 23, 42), (37, 99, 235), (255, 255, 255), (148, 163, 184), (96, 165, 250)

# first font pair that exists on this computer (Windows, macOS, Linux)
FONT_PAIRS = [
    (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf"),
    (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
BOLD = next((b for b, _ in FONT_PAIRS if Path(b).is_file()), None)
if BOLD is None:
    sys.exit("No usable TrueType font found. Edit FONT_PAIRS in tools/make_og_images.py.")


def font(size):
    return ImageFont.truetype(BOLD, size)


def wrap(draw, text, fnt, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            # don't strand a tiny word ("SG", "in", "&") at the end of a line: carry it to the next line
            parts = current.split(" ")
            if len(parts) > 1 and len(parts[-1]) <= 2:
                lines.append(" ".join(parts[:-1]))
                current = f"{parts[-1]} {word}"
            else:
                lines.append(current)
                current = word
    lines.append(current)
    return lines


def og_image(out, h1):
    img = Image.new("RGB", (1200, 630), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, 630], fill=ACCENT)                 # accent bar on the left edge
    d.text((80, 56), BRAND, font=font(34), fill=MUTED)        # brand, small, at the top
    size = 84
    while True:                                               # shrink the H1 until it fits in 4 lines
        fnt = font(size)
        lines = wrap(d, h1, fnt, 1040)
        if len(lines) <= 4 or size <= 48:
            break
        size -= 4
    line_height = int(size * 1.22)
    y = 335 - (len(lines) * line_height) // 2
    for line in lines:
        d.text((80, y), line, font=fnt, fill=WHITE)
        y += line_height
    img.save(out, "JPEG", quality=88, optimize=True)


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
        h1 = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", text, re.S).group(1)))
        out = ROOT / urlparse(img_url).path.lstrip("/")
        og_image(out, h1)
        print(f"{out.stat().st_size // 1024:4d} KB  {out.relative_to(ROOT).as_posix()}")

    logo(ROOT / "images" / "logo.png")
    print("      images/logo.png")


if __name__ == "__main__":
    main()
