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

## Going live later
Remove `<meta name="robots" content="noindex, nofollow">` from every page and change
`Disallow: /` to `Allow: /` in robots.txt.
