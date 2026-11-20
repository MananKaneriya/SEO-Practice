"""SEO checker for the plain-HTML Ortheon AI practice site.

Run from anywhere:   python tools/check_seo.py
Only needs Python 3 (no packages). Exit code 0 = everything passes, 1 = something failed.

Per-page table:  title length (50-60), description length (150-160), keywords present,
                 canonical == og:url == the page's own URL, og:image file exists, h1 count,
                 word count of the page copy, listed in sitemap.xml, brackets/todo left over.

Also checks:     every <a href> points to a real page (or #), no placeholder text anywhere,
                 FAQPage schema == visible FAQ, JSON-LD types per page type, heading order,
                 breadcrumb schema == visible breadcrumb, OG/Twitter tags, image size and
                 dimensions, banned wording (delivery / dealer / supplier / MOQ ...),
                 sentences copied between city/area pages, robots.txt and sitemap.xml.
"""
import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SITE_URL = "https://seo-practice.vercel.app"
BRAND = "Ortheon AI"
# the misspelt brand that must not appear in any file or file name (written in two halves
# so that this script does not contain the text it is hunting for)
OLD_BRAND = "ot" + "theon"
ROOT = Path(__file__).resolve().parent.parent
TITLE_RANGE, DESC_RANGE = (50, 60), (150, 160)
MIN_WORDS = {"city": 400, "area": 300}
PAGE_MIN_WORDS = {"locations/gujarat/ahmedabad/index.html": 500}   # the main ranking page

AHM = "/locations/gujarat/ahmedabad/"
CTA_LINK = ("/contact/", "Book a free demo")

# Ahmedabad location SEO plan: exact values for the three pages
PLAN = {
    "locations/gujarat/ahmedabad/index.html": dict(
        meta={
            "title": "WhatsApp Chatbot & CRM Software in Ahmedabad | Ortheon AI",
            "description": "WhatsApp AI chatbot and lead management software for Ahmedabad businesses. Reply 24/7 in Gujarati, Hindi & English and never miss a lead. Book a free demo.",
            "keywords": "whatsapp chatbot ahmedabad, ai chatbot ahmedabad, crm software ahmedabad, lead management software ahmedabad, customer support automation ahmedabad, ortheon ai",
            "og:title": "AI Chatbot & Lead Management for Ahmedabad Businesses",
            "og:description": "Reply to customers 24/7 and follow up every lead. Built for Ahmedabad businesses. Free demo.",
            "og:image": SITE_URL + "/images/og/whatsapp-chatbot-crm-ahmedabad.jpg",
            "og:image:alt": "Ortheon AI chatbot and CRM dashboard for businesses in Ahmedabad",
        },
        crumbs=["Home", "Gujarat", "Ahmedabad"], area_served="Ahmedabad", faqs=4,
        headings=[
            (1, "WhatsApp AI Chatbot & Lead Management Software in Ahmedabad"),
            (2, "AI App 1 – 24/7 Customer Support for Ahmedabad Businesses"),
            (2, "AI App 2 – Lead Management & Sales Follow-up in Ahmedabad"),
            (2, "Industries We Help in Ahmedabad"),
            (2, "Areas We Serve in Ahmedabad"),
            (2, "Setup, Training & Support in Ahmedabad"),
            (2, "Why Ahmedabad Businesses Choose Ortheon AI"),
            (2, "FAQs – AI Chatbot & CRM in Ahmedabad"),
        ]),
    "locations/gujarat/ahmedabad/bopal/index.html": dict(
        meta={
            "title": "WhatsApp Chatbot & CRM in Bopal, Ahmedabad | Ortheon AI",
            "description": "AI chatbot and lead management for Bopal businesses – real estate, clinics, schools and retail. Reply to every enquiry 24/7 in Gujarati. Book a free demo.",
            "keywords": "whatsapp chatbot bopal, ai chatbot bopal ahmedabad, crm software bopal, lead management bopal, chatbot for real estate bopal",
            "og:title": "AI Chatbot & CRM for Businesses in Bopal, Ahmedabad",
            "og:description": "Never miss a site-visit or appointment enquiry. AI chatbot and CRM for Bopal businesses.",
            "og:image": SITE_URL + "/images/og/whatsapp-chatbot-crm-bopal-ahmedabad.jpg",
            "og:image:alt": "Ortheon AI chatbot answering a site-visit enquiry for a Bopal real estate project",
        },
        crumbs=["Home", "Gujarat", "Ahmedabad", "Bopal"], area_served="Bopal, Ahmedabad", faqs=3,
        headings=[
            (1, "WhatsApp AI Chatbot & CRM for Businesses in Bopal, Ahmedabad"),
            (2, "AI App 1 for Bopal Real Estate, Clinics & Schools"),
            (2, "AI App 2 – Never Miss a Site-Visit or Admission Lead"),
            (2, "Types of Businesses We Help in Bopal"),
            (2, "Setup & Support Near Bopal"),
            (2, "Nearby Areas We Serve"),
            (2, "FAQs – AI Chatbot in Bopal"),
        ]),
    "locations/gujarat/ahmedabad/sg-highway/index.html": dict(
        meta={
            "title": "AI Chatbot & CRM on SG Highway, Ahmedabad | Ortheon AI",
            "description": "AI chatbot and lead management software for SG Highway offices, IT firms, showrooms and developers. Capture every lead and reply 24/7. Book a free demo.",
            "keywords": "ai chatbot sg highway, crm software sg highway ahmedabad, whatsapp chatbot sg highway, lead management sg highway, sales crm ahmedabad",
            "og:title": "AI Chatbot & CRM for SG Highway Businesses, Ahmedabad",
            "og:description": "Capture and follow up every lead from your SG Highway office or showroom. Free demo.",
            "og:image": SITE_URL + "/images/og/whatsapp-chatbot-crm-sg-highway-ahmedabad.jpg",
            "og:image:alt": "Ortheon AI lead dashboard for a sales team on SG Highway, Ahmedabad",
        },
        crumbs=["Home", "Gujarat", "Ahmedabad", "SG Highway"], area_served="SG Highway, Ahmedabad", faqs=3,
        headings=[
            (1, "WhatsApp AI Chatbot & CRM for Businesses on SG Highway, Ahmedabad"),
            (2, "AI App 1 for SG Highway Offices & Showrooms"),
            (2, "AI App 2 – Lead Scoring & Follow-up for Sales Teams"),
            (2, "Types of Businesses We Help on SG Highway"),
            (2, "Setup & Support Near SG Highway"),
            (2, "Nearby Areas We Serve"),
            (2, "FAQs – AI CRM on SG Highway"),
        ]),
}

# internal linking plan: (href, exact anchor text) that must exist on each page
REQUIRED_LINKS = {
    "locations/gujarat/index.html": [(AHM, "WhatsApp chatbot & CRM in Ahmedabad")],
    "locations/gujarat/ahmedabad/index.html": [
        (AHM + "bopal/", "AI chatbot in Bopal"),
        (AHM + "sg-highway/", "CRM for SG Highway businesses"),
        ("/ai-app-1/", "WhatsApp AI chatbot (AI App 1)"),
        ("/ai-app-2/", "lead management software (AI App 2)"),
        CTA_LINK],
    "locations/gujarat/ahmedabad/bopal/index.html": [
        (AHM + "sg-highway/", "SG Highway"), (AHM, "Ahmedabad"), CTA_LINK],
    "locations/gujarat/ahmedabad/sg-highway/index.html": [
        (AHM + "bopal/", "Bopal"), (AHM, "Ahmedabad"), CTA_LINK],
}
# plain-text (not linked) names required in the "Nearby Areas We Serve" lists of the two area pages
NEARBY_PLAIN = {
    "locations/gujarat/ahmedabad/bopal/index.html": ["South Bopal", "Shela", "Ghuma", "Thaltej"],
    "locations/gujarat/ahmedabad/sg-highway/index.html": ["Bodakdev", "Thaltej", "Prahlad Nagar", "Science City"],
}
MAX_IMAGE_KB = 300
VOID = {"meta", "link", "br", "input", "img", "hr"}

# wording that belongs to the old "manufacturer / dealer" site and must not come back
BANNED = [
    (r"\bdeliver(?:y|ies|s|ed|ing)?\b", "delivery wording"),
    (r"(?<!automobile )\bdealers?\b", "dealer wording"),
    (r"\bsuppliers?\b", "supplier wording"),
    (r"\bMOQ\b", "MOQ"),
    (r"\bfactory\b", "factory wording"),
    (r"\btestimonials?\b", "testimonial"),
    (r"₹|\bRs\.?\s?\d|\bINR\b", "price"),
    (r"\b\d{10}\b|\+91", "phone number"),
]
PLACEHOLDERS = [r"\btodo\b", r"Product 1", r"Product 2", r"example\.com", r"\[Brand\]"]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.meta, self.canonical = "", {}, None
        self.stylesheet = None
        self.jsonld = []
        self.hrefs = []
        self.headings = []          # [(level, text)]
        self.crumb = []             # visible breadcrumb [(text, href|None)]
        self.dt, self.dd = [], []   # visible FAQ
        self.main_words = []        # words of page copy (areas / towns lists excluded)
        self.main_text = []         # sentences source
        self._cap = None            # what text we are collecting right now
        self._buf = ""
        self._in_main = False
        self._excl = None           # [tag, depth] while inside an excluded block
        self._nav = False
        self._nav_buf = ""
        self._a = None
        self.anchors = []           # every link on the page: [(href, anchor text)]
        self._anchor = None
        self.lists = {}             # text of <li> items under each h2, e.g. "Nearby Areas We Serve" -> [(text, linked?)]
        self._h2 = None
        self._li = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "title":
            self._cap, self._buf = "title", ""
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            if a.get("rel") == "canonical":
                self.canonical = a.get("href")
            if a.get("rel") == "stylesheet":
                self.stylesheet = a.get("href")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._cap, self._buf = "ld", ""
        elif tag == "main":
            self._in_main = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._cap, self._buf = "h", ""
            self._h = int(tag[1])
        elif tag in ("dt", "dd"):
            self._cap, self._buf = tag, ""
        elif tag == "nav" and "breadcrumb" in cls:
            self._nav, self._nav_buf = True, ""
        elif tag == "a":
            if a.get("href") is not None:
                self.hrefs.append(a["href"])
            self._anchor = [a.get("href"), ""]
            if self._li is not None:
                self._li[1] = True
            if self._nav:
                self._a = [a.get("href"), ""]
        elif tag == "li" and self._in_main:
            self._li = ["", False]
        if self._in_main:
            if self._excl:
                if tag == self._excl[0]:
                    self._excl[1] += 1
            elif (tag == "ul" and "areas" in cls) or (tag == "p" and "towns" in cls):
                self._excl = [tag, 1]

    def handle_endtag(self, tag):
        if tag == "a" and self._anchor is not None:
            self.anchors.append((self._anchor[0], " ".join(self._anchor[1].split())))
            self._anchor = None
        if tag == "li" and self._li is not None:
            self.lists.setdefault(self._h2, []).append((" ".join(self._li[0].split()), self._li[1]))
            self._li = None
        if self._cap == "title" and tag == "title":
            self.title, self._cap = self._buf.strip(), None
        elif self._cap == "ld" and tag == "script":
            self.jsonld.append(self._buf)
            self._cap = None
        elif self._cap == "h" and tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append((self._h, " ".join(self._buf.split())))
            if self._h == 2:
                self._h2 = " ".join(self._buf.split())
            self._cap = None
        elif self._cap == tag and tag in ("dt", "dd"):
            (self.dt if tag == "dt" else self.dd).append(" ".join(self._buf.split()))
            self._cap = None
        elif tag == "a" and self._nav and self._a:
            self.crumb.append((self._a[1].strip(), self._a[0]))
            self._nav_buf += "\0"
            self._a = None
        elif tag == "nav" and self._nav:
            self._nav = False
            tail = self._nav_buf.split("\0")[-1].replace("›", "").strip()
            if tail:
                self.crumb.append((tail, None))
        elif tag == "main":
            self._in_main = False
        if self._excl and tag == self._excl[0] and tag not in VOID:
            self._excl[1] -= 1
            if self._excl[1] == 0:
                self._excl = None

    def handle_data(self, data):
        if self._anchor is not None:
            self._anchor[1] += data
        if self._li is not None:
            self._li[0] += data
        if self._cap:
            self._buf += data
        if self._nav:
            if self._a is not None:
                self._a[1] += data
            else:
                self._nav_buf += data
        if self._in_main and not self._excl and self._cap != "ld":
            self.main_words += re.findall(r"[A-Za-z0-9][\w'’/-]*", data)
            self.main_text.append(data)


def kind_of(rel):
    parts = rel.split("/")[:-1]
    if not parts:
        return "home"
    if parts[0] in ("ai-app-1", "ai-app-2"):
        return "product"
    if parts[0] == "contact":
        return "contact"
    return {2: "hub", 3: "city", 4: "area"}[len(parts)]


def own_url(rel):
    folder = "/".join(rel.split("/")[:-1])
    return SITE_URL + "/" + (folder + "/" if folder else "")


def jpeg_size(path):
    data = path.read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def png_size(path):
    return struct.unpack(">II", path.read_bytes()[16:24])


def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from walk_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_strings(v)


def schema_list(p):
    out = []
    for raw in p.jsonld:
        data = json.loads(raw)
        out.append(data)
    return out


def main():
    pages = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts and "node_modules" not in p.parts)
    # folder of every index.html, as a link target: "" is the home page, "contact" is /contact/, ...
    existing = {"" if p.parent == ROOT else p.parent.relative_to(ROOT).as_posix() for p in pages}
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    in_sitemap = set(re.findall(r"<loc>\s*(.*?)\s*</loc>", sitemap))
    problems, rows, parsed = [], [], {}
    place_names = set()

    # first pass: parse + collect place names (for the copied-sentence check)
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        p = Page()
        p.feed(page.read_text(encoding="utf-8"))
        parsed[rel] = p
        for name, _ in p.crumb:
            if name not in ("Home", "Gujarat", "Contact") and not name.startswith("AI App"):
                place_names.add(name)

    sentences = {}  # normalised sentence -> set of pages
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        p, kind, url = parsed[rel], kind_of(rel), own_url(rel)
        raw = page.read_text(encoding="utf-8")
        bad = lambda ok, msg: None if ok else problems.append(f"{rel}: {msg}")

        # --- head tags
        og_url, og_img = p.meta.get("og:url"), p.meta.get("og:image", "")
        urls_ok = p.canonical == og_url == url
        img_path = ROOT / urlparse(og_img).path.lstrip("/")
        img_ok = og_img.startswith(SITE_URL + "/images/og/") and img_path.is_file()
        h1s = [t for lvl, t in p.headings if lvl == 1]
        t_len, d_len = len(p.title), len(p.meta.get("description", ""))
        words = len(p.main_words)
        in_map = url in in_sitemap
        has_kw = bool(p.meta.get("keywords", "").strip())

        # --- leftovers: brackets / todo / placeholders (JSON-LD handled separately)
        no_ld = re.sub(r'<script type="application/ld\+json">.*?</script>', "", raw, flags=re.S)
        left = len(re.findall(r"[\[\]]", no_ld))
        left += sum(len(re.findall(rx, raw, flags=re.I)) for rx in PLACEHOLDERS)
        ld_data = schema_list(p)
        for obj in ld_data:
            for s in walk_strings(obj):
                if re.search(r"[\[\]]", s) or any(re.search(rx, s, re.I) for rx in PLACEHOLDERS):
                    left += 1
        rows.append((rel, t_len, d_len, has_kw, urls_ok, img_ok, len(h1s), words, in_map, left))

        bad(urls_ok, f"canonical / og:url / own URL differ ({p.canonical} | {og_url} | {url})")
        bad(img_ok, f"og:image file missing: {og_img}")
        bad(TITLE_RANGE[0] <= t_len <= TITLE_RANGE[1], f"title is {t_len} chars (want {TITLE_RANGE[0]}-{TITLE_RANGE[1]})")
        bad(DESC_RANGE[0] <= d_len <= DESC_RANGE[1], f"description is {d_len} chars (want {DESC_RANGE[0]}-{DESC_RANGE[1]})")
        bad(p.meta.get("description", "").rstrip(".").lower().endswith(("demo", "demo today")), "description does not end with the free-demo call to action")
        bad(has_kw, "no meta keywords")
        bad(len(h1s) == 1, f"{len(h1s)} <h1> tags")
        bad(in_map, "not in sitemap.xml")
        bad(left == 0, f"{left} bracket/todo/placeholder leftovers")
        bad(p.meta.get("robots") == "noindex, nofollow", "robots meta is not 'noindex, nofollow'")
        bad(p.meta.get("author") == BRAND, f"meta author is not {BRAND}")
        bad(p.stylesheet == "/css/style.css", "stylesheet link missing")
        bad(p.meta.get("og:type") == "website" and p.meta.get("og:site_name") == BRAND and p.meta.get("og:locale") == "en_IN",
            "og:type / og:site_name / og:locale wrong")
        bad(p.meta.get("og:image:width") == "1200" and p.meta.get("og:image:height") == "630" and p.meta.get("og:image:alt"),
            "og:image width/height/alt wrong")
        bad(p.meta.get("og:title") == p.meta.get("twitter:title") and p.meta.get("og:title"), "og:title != twitter:title")
        bad(p.meta.get("og:description") == p.meta.get("twitter:description") and 0 < len(p.meta.get("og:description", "")) < 120,
            "og/twitter description missing, different or 120+ chars")
        bad(p.meta.get("twitter:card") == "summary_large_image" and p.meta.get("twitter:image") == og_img, "twitter card/image wrong")
        bad("<title>" in raw and raw.index("<title>") < raw.index('name="description"') < raw.index('name="keywords"')
            < raw.index('name="robots"') < raw.index('name="author"') < raw.index('rel="canonical"')
            < raw.index('property="og:type"') < raw.index('name="twitter:card"') < raw.index('rel="stylesheet"')
            < raw.index("application/ld+json"), "head tags are not in the required order")

        # --- image file: size and dimensions
        if img_path.is_file():
            kb = img_path.stat().st_size / 1024
            bad(kb <= MAX_IMAGE_KB, f"{img_path.name} is {kb:.0f} KB (max {MAX_IMAGE_KB})")
            bad(jpeg_size(img_path) == (1200, 630), f"{img_path.name} is {jpeg_size(img_path)}, not 1200x630")

        # --- headings: one h1, never skip a level
        lv = [l for l, _ in p.headings]
        bad(bool(lv) and lv[0] == 1 and all(b <= a + 1 for a, b in zip(lv, lv[1:])), f"heading levels out of order: {lv}")

        # --- word count minimums (city 400+, area 300+)
        need = PAGE_MIN_WORDS.get(rel, MIN_WORDS.get(kind))
        if need:
            bad(words >= need, f"only {words} words of copy (this page needs {need}+)")

        # --- the Ahmedabad SEO plan: exact values, heading order, breadcrumb, areaServed
        spec = PLAN.get(rel)
        if spec:
            got = {"title": p.title, **{k: p.meta.get(k) for k in spec["meta"] if k != "title"}}
            for key, want in spec["meta"].items():
                bad(got[key] == want, f"{key} differs from the plan:\n        got  {got[key]!r}\n        want {want!r}")
            bad(p.meta.get("twitter:title") == spec["meta"]["og:title"]
                and p.meta.get("twitter:description") == spec["meta"]["og:description"]
                and p.meta.get("twitter:image") == spec["meta"]["og:image"], "twitter:* must equal og:title / og:description / og:image")
            bad(p.headings == spec["headings"], f"headings differ from the plan:\n        got  {p.headings}\n        want {spec['headings']}")
            svc = [d for d in ld_data if d.get("@type") == "Service"]
            if svc:
                served = svc[0].get("areaServed", {}).get("name")
                bad(served == spec["area_served"], f"Service areaServed is {served!r}, plan says {spec['area_served']!r}")
                bad(svc[0].get("serviceType") == "AI customer support and sales software"
                    and svc[0].get("provider", {}).get("name") == BRAND, "Service serviceType/provider wrong")
            bad([n for n, _ in p.crumb] == spec["crumbs"], f"breadcrumb names {[n for n, _ in p.crumb]} != {spec['crumbs']}")
            bad(len(p.dt) == spec["faqs"], f"{len(p.dt)} FAQs, plan says {spec['faqs']}")
            order = [d.get("@type") for d in ld_data]
            bad(order == ["BreadcrumbList", "Service", "FAQPage"], f"JSON-LD order is {order}, plan says BreadcrumbList, Service, FAQPage")
            bad(not re.search(r'class="todo"', raw), "class=todo element left")

        # --- internal linking plan: these links, with exactly this anchor text
        for href, text in REQUIRED_LINKS.get(rel, []):
            bad((href, text) in p.anchors, f"missing link: anchor {text!r} -> {href}")
        # "Nearby Areas We Serve" on the two area pages: linked sibling + plain-text others
        if rel in NEARBY_PLAIN:
            items = p.lists.get("Nearby Areas We Serve", [])
            plain = [t for t, linked in items if not linked]
            bad(plain == NEARBY_PLAIN[rel], f"nearby plain-text areas are {plain}, plan says {NEARBY_PLAIN[rel]}")
            bad(sum(1 for _, linked in items if linked) == 1, "exactly one nearby area should be linked")
        # no vague anchors anywhere
        for href, text in p.anchors:
            bad(text.lower() not in ("click here", "here", "read more", "more", "link"), f"vague anchor text {text!r} -> {href}")

        # --- links: every <a href> must resolve
        for h in p.hrefs:
            if h.startswith("#"):
                continue
            if re.match(r"[a-z]+:", h):
                continue  # external - not checked
            if not h.startswith("/"):
                bad(False, f"relative link {h!r} (use root-relative /path/)")
                continue
            path = urlparse(h).path
            target = path.strip("/")
            ok = (target in existing) if path.endswith("/") else (ROOT / target).is_file()
            bad(ok, f"broken link {h}")

        # --- visible breadcrumb == BreadcrumbList schema
        crumbs = [d for d in ld_data if d.get("@type") == "BreadcrumbList"]
        bad(len(crumbs) == 1, "needs exactly one BreadcrumbList")
        if crumbs:
            items = sorted(crumbs[0]["itemListElement"], key=lambda i: i["position"])
            schema = [(i["name"], i["item"]) for i in items]
            visible = [(t, SITE_URL + h if h else url) for t, h in p.crumb]
            bad([i["position"] for i in items] == list(range(1, len(items) + 1)), "breadcrumb positions not 1..n")
            bad(visible == schema, f"visible breadcrumb != schema ({visible} vs {schema})")

        # --- JSON-LD types required per page type
        types = [d.get("@type") for d in ld_data]
        want = {"home": {"Organization"}, "hub": {"Organization", "FAQPage"}, "product": {"SoftwareApplication", "FAQPage"},
                "city": {"Service", "FAQPage"}, "area": {"Service", "FAQPage"}, "contact": set()}[kind] | {"BreadcrumbList"}
        bad(set(types) == want and len(types) == len(want), f"JSON-LD types {types}, expected {sorted(want)}")
        for d in ld_data:
            if d.get("@type") == "SoftwareApplication":
                bad(d.get("applicationCategory") == "BusinessApplication" and d.get("operatingSystem") == "Web, Android, iOS"
                    and "offers" not in d and "aggregateRating" not in d, "SoftwareApplication fields wrong")
            if d.get("@type") == "Organization":
                bad(d.get("logo") == SITE_URL + "/images/logo.png" and d.get("areaServed"), "Organization logo/areaServed wrong")
            bad("offers" not in d and "aggregateRating" not in d and "review" not in d, "price/rating/review markup is not allowed")

        # --- FAQPage == visible FAQ (questions AND answers, same order)
        faq = [d for d in ld_data if d.get("@type") == "FAQPage"]
        if faq:
            sq = [e["name"] for e in faq[0]["mainEntity"]]
            sa = [" ".join(e["acceptedAnswer"]["text"].split()) for e in faq[0]["mainEntity"]]
            bad(sq == p.dt and sa == p.dd, "FAQPage schema does not match the visible FAQ")
        else:
            bad(not p.dt, "visible FAQ but no FAQPage schema")

        # --- banned wording in visible text
        visible_text = " ".join(p.main_text)
        for rx, label in BANNED:
            if re.search(rx, visible_text, re.I):
                bad(False, f"banned wording ({label}): {re.search(rx, visible_text, re.I).group(0)!r}")

        # --- sentences for the copied-copy check (city + area pages only)
        if kind in ("city", "area"):
            norm = " ".join(visible_text.split())
            for name in sorted(place_names, key=len, reverse=True):
                norm = norm.replace(name, "X")
            for s in re.split(r"(?<=[.!?])\s+", norm):
                if len(s.split()) >= 8 and not s.startswith("←"):  # the back link is navigation, not copy
                    sentences.setdefault(s.lower(), set()).add(rel)

    # --- copied sentences between city/area pages
    for s, where in sentences.items():
        if len(where) > 1:
            problems.append(f"same sentence on {len(where)} location pages ({', '.join(sorted(where))}): {s[:90]}...")

    # --- site-wide files
    for rel in sorted(in_sitemap - {own_url(p.relative_to(ROOT).as_posix()) for p in pages}):
        problems.append(f"sitemap.xml lists {rel} but no index.html exists for it")
    for u in in_sitemap:
        if not (u.startswith(SITE_URL + "/") and u.endswith("/")):
            problems.append(f"sitemap.xml URL not absolute with trailing slash: {u}")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8").splitlines()
    if "User-agent: *" not in robots or "Disallow: /" not in robots or f"Sitemap: {SITE_URL}/sitemap.xml" not in robots:
        problems.append("robots.txt must contain User-agent: *, Disallow: / and the Sitemap line")
    logo = ROOT / "images" / "logo.png"
    if not logo.is_file() or png_size(logo) != (512, 512):
        problems.append("images/logo.png missing or not 512x512")

    # --- placeholder text in ANY html / css / txt / xml file
    for f in sorted(ROOT.rglob("*")):
        if f.is_file() and ".git" not in f.parts and "tools" not in f.parts and f.suffix in (".html", ".css", ".xml", ".txt"):
            t = f.read_text(encoding="utf-8")
            if f.suffix == ".html":
                t = re.sub(r'<script type="application/ld\+json">.*?</script>', "", t, flags=re.S)
                if re.search(r"[\[\]]", t):
                    problems.append(f"{f.relative_to(ROOT).as_posix()}: contains [ or ]")
            for rx in PLACEHOLDERS:
                if re.search(rx, t, re.I):
                    problems.append(f"{f.relative_to(ROOT).as_posix()}: contains placeholder text /{rx}/")

    # --- the misspelt brand must not appear in ANY file (tools and README included) or file name
    for f in sorted(ROOT.rglob("*")):
        if ".git" in f.parts:
            continue
        rel_f = f.relative_to(ROOT).as_posix()
        if OLD_BRAND in rel_f.lower():
            problems.append(f"{rel_f}: file name uses the old brand spelling")
        if f.is_file() and f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".gif", ".ico", ".pyc"):
            try:
                if OLD_BRAND in f.read_text(encoding="utf-8").lower():
                    problems.append(f"{rel_f}: contains the old brand spelling")
            except UnicodeDecodeError:
                pass

    # --- the plan says: no new Ahmedabad area pages beyond Bopal and SG Highway
    ahm_dir = ROOT / "locations" / "gujarat" / "ahmedabad"
    ahm_areas = {d.name for d in ahm_dir.iterdir() if d.is_dir()}
    if ahm_areas != {"bopal", "sg-highway"}:
        problems.append(f"Ahmedabad area pages must be exactly bopal and sg-highway, found {sorted(ahm_areas)}")

    # --- print the table
    head = ("path", "title", "desc", "keywords", "urls match", "og:image", "h1", "words", "sitemap", "brackets/todo")
    yn = lambda v: "yes" if v else "NO"
    table = [head] + [(r[0], r[1], r[2], yn(r[3]), yn(r[4]), yn(r[5]), r[6], r[7], yn(r[8]), r[9]) for r in rows]
    widths = [max(len(str(row[i])) for row in table) for i in range(len(head))]
    for n, row in enumerate(table):
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())
        if n == 0:
            print("  ".join("-" * w for w in widths))
    print("\nurls match = canonical == og:url == the page's own URL. words = page copy only (area/town lists not counted).")

    if problems:
        print(f"\nFAILED ({len(problems)}):")
        for m in problems:
            print("  -", m)
        return 1
    print(f"\nAll checks passed on {len(pages)} pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
