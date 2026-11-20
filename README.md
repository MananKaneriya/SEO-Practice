# Gujarat location pages – SEO practice site (plain HTML)

## Open it
1. VS Code → File → Open Folder → choose this `seo-practice` folder (it must be the root).
2. Install the "Live Server" extension → right-click `index.html` → Open with Live Server.
3. Go to http://127.0.0.1:5500/locations/gujarat/

## Files
- locations/gujarat/index.html            Hub: all 34 districts, cities, areas
- locations/gujarat/<city>/index.html     City pages: ahmedabad, surat, vadodara, rajkot
- locations/gujarat/<city>/<area>/        Area pages: ahmedabad/sg-highway, surat/vesu
- sitemap.xml, robots.txt                 For Google (replace example.com)
- css/style.css                           Basic styling

## To do
- Find & replace (Ctrl+Shift+H): [Product 1], [Product 2], [Brand], example.com
- Replace every yellow "todo" box with real, unique text for that city
- New city: copy a city folder, rename it, edit title/meta/h1/canonical/breadcrumb/areas,
  link it from the hub, add it to sitemap.xml
