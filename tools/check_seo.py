"""SEO checker for the plain-HTML practice site.

Run from anywhere:   python tools/check_seo.py
Needs only Python 3 (no packages). Exit code 0 = all hard checks pass, 1 = something failed.

Hard checks (FAIL):  canonical == og:url == page URL, og:image file exists,
                     exactly one <h1>, page is in sitemap.xml, breadcrumb schema == visible
                     breadcrumb, twitter:image == og:image, internal /locations/ links work.
Soft checks (warn):  title 50-60 chars, description 150-160 chars. They are only a target;
                     with short placeholder names like [Brand] they will often be under.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SITE_URL = "https://seo-practice.vercel.app"
ROOT = Path(__file__).resolve().parent.parent
TITLE_RANGE = (50, 60)
DESC_RANGE = (150, 160)


class PageParser(HTMLParser):
    """Collects the bits of a page we care about."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta = {}        # name=/property= -> content
        self.canonical = None
        self.h1 = 0
        self.jsonld = []
        self.hrefs = []
        self.crumb = []       # visible breadcrumb: [(text, href or None)]
        self._in = None
        self._buf = ""
        self._nav = False
        self._a_href = None
        self._a_text = ""
        self._nav_text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in, self._buf = "title", ""
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in, self._buf = "ld", ""
        elif tag == "nav" and "breadcrumb" in (a.get("class") or ""):
            self._nav, self._nav_text = True, ""
        elif tag == "a":
            if a.get("href"):
                self.hrefs.append(a["href"])
            if self._nav:
                self._a_href, self._a_text = a.get("href"), ""

    def handle_endtag(self, tag):
        if tag == "title" and self._in == "title":
            self.title, self._in = self._buf.strip(), None
        elif tag == "script" and self._in == "ld":
            self.jsonld.append(self._buf)
            self._in = None
        elif tag == "a" and self._nav and self._a_href is not None:
            self.crumb.append((self._a_text.strip(), self._a_href))
            self._nav_text += "\0"  # marks where the link was
            self._a_href = None
        elif tag == "nav" and self._nav:
            self._nav = False
            # the last crumb is plain text (the current page): text after the last link
            tail = self._nav_text.split("\0")[-1].replace("›", "").strip()
            if tail:
                self.crumb.append((tail, None))

    def handle_data(self, data):
        if self._in:
            self._buf += data
        if self._nav:
            if self._a_href is not None:
                self._a_text += data
            else:
                self._nav_text += data


def url_for(page):
    rel = page.parent.relative_to(ROOT).as_posix()
    return SITE_URL + "/" + ("" if rel == "." else rel + "/")


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return set(re.findall(r"<loc>\s*(.*?)\s*</loc>", xml))


def schema_crumbs(p):
    """[(name, absolute url)] from the BreadcrumbList JSON-LD, or None if missing/invalid."""
    for raw in p.jsonld:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if data.get("@type") == "BreadcrumbList":
            items = sorted(data["itemListElement"], key=lambda i: i["position"])
            if [i["position"] for i in items] != list(range(1, len(items) + 1)):
                return None
            return [(i["name"], i["item"]) for i in items]
    return None


def crumbs_match(p, own_url):
    schema = schema_crumbs(p)
    if not schema:
        return False
    # visible: links are root-relative, the last item has no link (it is the current page)
    visible = [(t, SITE_URL + h if h else own_url) for t, h in p.crumb]
    return visible == schema


def check_links(p, page, indexes):
    """Every href="/locations/..." must resolve to an existing index.html."""
    bad = []
    for h in p.hrefs:
        if h.startswith("/locations/"):
            target = ROOT / urlparse(h).path.strip("/") / "index.html"
            if target not in indexes:
                bad.append(h)
    return bad


def main():
    pages = sorted(p for p in ROOT.rglob("index.html")
                   if ".git" not in p.parts and "node_modules" not in p.parts)
    indexes = set(pages)
    in_sitemap = sitemap_urls()
    rows, problems = [], []

    for page in pages:
        p = PageParser()
        p.feed(page.read_text(encoding="utf-8"))
        own = url_for(page)
        rel = page.relative_to(ROOT).as_posix()
        og_url, og_img = p.meta.get("og:url"), p.meta.get("og:image", "")
        urls_ok = p.canonical == og_url == own
        img_path = ROOT / urlparse(og_img).path.lstrip("/")
        img_ok = og_img.startswith(SITE_URL + "/") and img_path.is_file()
        tw_ok = p.meta.get("twitter:image") == og_img
        t_len, d_len = len(p.title), len(p.meta.get("description", ""))
        has_kw = bool(p.meta.get("keywords", "").strip())
        in_map = own in in_sitemap
        crumb_ok = crumbs_match(p, own)
        bad_links = check_links(p, page, indexes)

        rows.append((rel, t_len, d_len, has_kw, urls_ok, img_ok, p.h1, in_map, crumb_ok, tw_ok, not bad_links))

        for ok, msg in [
            (urls_ok, f"canonical/og:url/page URL differ (canonical={p.canonical}, og:url={og_url}, expected={own})"),
            (img_ok, f"og:image file missing: {og_img}"),
            (p.h1 == 1, f"{p.h1} <h1> tags"),
            (in_map, "not in sitemap.xml"),
            (has_kw, "no meta keywords"),
            (crumb_ok, "breadcrumb schema != visible breadcrumb"),
            (tw_ok, "twitter:image != og:image"),
            (not bad_links, f"broken internal links: {bad_links}"),
            (p.meta.get("robots") == "noindex, nofollow", "robots meta is not 'noindex, nofollow'"),
            ("example.com" not in page.read_text(encoding="utf-8"), "still contains example.com"),
        ]:
            if not ok:
                problems.append(f"{rel}: {msg}")

    def mark(v):
        return "yes" if v else "NO"

    def length(n, rng):
        return f"{n}{'' if rng[0] <= n <= rng[1] else '*'}"

    head = ("path", "title", "desc", "kw", "urls=", "og img", "h1", "sitemap", "crumbs", "tw img", "links")
    table = [head] + [(r[0], length(r[1], TITLE_RANGE), length(r[2], DESC_RANGE), mark(r[3]), mark(r[4]),
                       mark(r[5]), str(r[6]) if r[6] == 1 else f"{r[6]}!", mark(r[7]), mark(r[8]),
                       mark(r[9]), mark(r[10])) for r in rows]
    widths = [max(len(str(row[i])) for row in table) for i in range(len(head))]
    for n, row in enumerate(table):
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
        if n == 0:
            print("  ".join("-" * w for w in widths))

    print("\n* = outside the target range (title 50-60, description 150-160). Soft warning only.")
    print("urls= means canonical == og:url == the page's own URL.")
    extra = in_sitemap - {url_for(p) for p in pages}
    if extra:
        problems += [f"sitemap.xml lists a URL with no index.html: {u}" for u in sorted(extra)]
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Disallow: /" not in robots.splitlines() or f"Sitemap: {SITE_URL}/sitemap.xml" not in robots:
        problems.append("robots.txt must have 'Disallow: /' and the Sitemap line")

    if problems:
        print("\nFAILED:")
        for m in problems:
            print("  -", m)
        return 1
    print(f"\nAll hard checks passed on {len(pages)} pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
