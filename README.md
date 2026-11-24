# Ortheon AI – Gujarat SEO practice site (plain HTML)

Static site, no frameworks and no build step. Deployed on Vercel from GitHub.
Every page is a plain `index.html`. All pages are `noindex, nofollow` because this is a practice site.

## Open it
1. VS Code → File → Open Folder → choose this `seo-practice` folder (it must be the root).
2. Install the "Live Server" extension → right-click `index.html` → Open with Live Server.
3. Go to http://127.0.0.1:5500/locations/gujarat/

## Files
- index.html                               Home
- ai-app-1/, ai-app-2/                     Product pages
- contact/                                 Book a free demo (form layout only, no backend)
- locations/gujarat/index.html             Hub: all 34 districts, cities, areas
- locations/gujarat/<city>/index.html      City pages: ahmedabad, surat, vadodara, rajkot
- locations/gujarat/<city>/<area>/         Area pages: ahmedabad/sg-highway, ahmedabad/bopal, surat/vesu
- articles/index.html                      Articles hub: lists every post
- articles/<slug>/index.html               One blog post each (see "Articles and backlinks" below)
- images/og/                               1200x630 social-share images (placeholders), one per page
- images/logo.png                          512x512 logo (placeholder)
- sitemap.xml, robots.txt                  robots.txt blocks everything while this is a practice site
- css/style.css                            Basic styling
- tools/check_seo.py                       SEO checker – run it before every push
- tools/make_og_images.py                  Rebuilds images/og/*.jpg and logo.png from each page's H1 (needs Pillow)

## Check your work
    python tools/check_seo.py
Prints one row per page (title/description length, canonical, og:image, h1, word count, sitemap)
and fails on broken links, leftover placeholders, FAQ/schema mismatches and copied text.

## Adding a new city or area
1. Copy an existing city/area folder, rename it, and write genuinely different copy for it.
2. Update the title, description, keywords, canonical, og:*, twitter:*, JSON-LD, breadcrumb and H1.
3. Add its og:image path to the page, then run `python tools/make_og_images.py` (1200x630 JPG, under 300 KB).
4. Link it from the hub / city page and add it to sitemap.xml.
5. Run `python tools/check_seo.py`.

## Articles and backlinks
Every article is written to do two jobs: be useful enough that other sites want to link to it, and pass
that link value on to a page that sells something. The three starter articles are a small topic cluster:
each links to a product or location page, to the demo page and to the other two articles, and the product
and home pages link back to them.

| Article | Link value goes to | Why another site would link to it | Anchor text to ask for |
|---|---|---|---|
| reply-to-whatsapp-enquiries-faster | /ai-app-1/ | Reply-time table and a seven-fix list | "how to reply to WhatsApp enquiries faster" |
| lead-scoring-hot-warm-cold | /ai-app-2/ | A scoring sheet people can copy | "lead scoring sheet" |
| lead-follow-up-checklist-ahmedabad | /locations/gujarat/ahmedabad/ (and its Bopal and SG Highway pages) | A checklist and a two-week timing plan | "lead follow-up checklist for Ahmedabad businesses" |

Ask for links to the article itself, not to the home page, and vary the anchor text between outreach emails.
Good places to ask: business and trade association newsletters, local SME and startup blogs, and Gujarat
business directories. Keep a log of who you asked, what page you asked them to link to, and the result.

**Backlinks do not count yet.** Every page is `noindex, nofollow`, so Google will not index the articles or
pass their link value on. Treat this as practice until you follow "Going live later" below.

### Adding a new article
1. Copy an existing `articles/<slug>/` folder. The slug is lowercase with hyphens and starts with the keyword.
2. Rewrite the copy (700+ words), then update `<title>` (max 45), description (max 115), keywords,
   canonical, `og:*`, `twitter:*`, the breadcrumb and the FAQ (visible text and FAQPage schema must match).
3. Set the dates in all three places: `article:published_time` / `article:modified_time`, the BlogPosting
   schema, and the visible `<time datetime>`. The BlogPosting `headline` must equal the H1.
4. Link to a product page, to `/contact/` ("Book a free demo") and to at least two other articles, and add
   the new post to the "Related Articles" list of the posts it relates to.
5. Add it to the list in `articles/index.html` **and** to that page's `ItemList` schema (same order),
   then add the URL to `sitemap.xml`.
6. Run `python tools/make_og_images.py` for the 1200x630 image, then `python tools/check_seo.py`.

## Going live later
Remove `<meta name="robots" content="noindex, nofollow">` from every page and change
`Disallow: /` to `Allow: /` in robots.txt.
