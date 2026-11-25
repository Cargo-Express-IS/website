#!/usr/bin/env python3
"""Build the cargoexpress.is website into dist/.

    python build.py            build once
    python build.py --serve    build, then serve dist/ at http://localhost:8000

On Netlify the CONTEXT environment variable says which build this is, and URL
is the site's main address. Search engines may only index the production build
served on the real domain (URL == base_url in content/site.json). Every other
build (local, deploy previews, branch deploys, and production on *.netlify.app
before the domain is connected) gets noindex and a blocking robots.txt.
"""

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

PAGES = ["home", "thanks", "privacy"]  # rendered once per language
LANGS = ["is", "en"]                   # first one is the main language

PLACEHOLDER = re.compile(r"\[[A-ZÁÐÉÍÓÚÝÞÆÖ0-9][A-ZÁÐÉÍÓÚÝÞÆÖ0-9 /:–\-,.()]{2,}[^\]\n]*\]")


def load(name):
    with open(CONTENT / name, encoding="utf-8") as f:
        return json.load(f)


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def fill(text, site):
    return (text.replace("{kennitala}", site["kennitala"])
                .replace("{info}", site["emails"]["info"]))


def out_path(url_path):
    """'/en/thanks/' -> dist/en/thanks/index.html"""
    rel = url_path.strip("/")
    return DIST / rel / "index.html" if rel else DIST / "index.html"


def main():
    site = load("site.json")
    production = (os.environ.get("CONTEXT") == "production"
                  and os.environ.get("URL", "").rstrip("/") == site["base_url"].rstrip("/"))
    strings = {lang: load(f"{lang}.json") for lang in LANGS}

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "svg"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    assets = {
        "css": f"/css/site.css?v={fingerprint(STATIC / 'css' / 'site.css')}",
        "js": f"/js/track.js?v={fingerprint(STATIC / 'js' / 'track.js')}",
    }

    # AWB prefix -> airline, only for confirmed prefixes
    prefixes = {a["awb_prefix"]: {"name": a["name"], "url": a["tracking_url"]}
                for a in site["airlines"] if a.get("awb_prefix")}

    for lang in LANGS:
        t = strings[lang]
        for page in PAGES:
            alternates = {l: site["base_url"] + strings[l]["paths"][page] for l in LANGS}
            other = "en" if lang == "is" else "is"
            ctx = dict(
                site=site, t=t, lang=lang, page=page, production=production,
                assets=assets, prefixes=prefixes,
                url=alternates[lang], alternates=alternates,
                other_lang=other, other_url=strings[other]["paths"][page],
                fill=lambda s: fill(s, site), year=date.today().year,
            )
            html = env.get_template(f"{page}.html").render(**ctx)
            dest = out_path(t["paths"][page])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")

    # 404 page (both languages on one page)
    t = strings[LANGS[0]]
    html = env.get_template("404.html").render(
        site=site, t=t, t_en=strings["en"], lang=LANGS[0], page="notfound",
        production=production, assets=assets, prefixes=prefixes,
        url=site["base_url"] + "/404", alternates={}, other_lang="en",
        other_url=strings["en"]["paths"]["home"], fill=lambda s: fill(s, site),
        year=date.today().year,
    )
    (DIST / "404.html").write_text(html, encoding="utf-8")

    # robots.txt and sitemap.xml
    if production:
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {site['base_url']}/sitemap.xml\n"
    else:
        robots = "User-agent: *\nDisallow: /\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    urls = []
    for page in ["home", "privacy"]:
        for lang in LANGS:
            loc = site["base_url"] + strings[lang]["paths"][page]
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{site["base_url"] + strings[l]["paths"][page]}"/>'
                for l in LANGS)
            urls.append(f"  <url>\n    <loc>{loc}</loc>{alts}\n  </url>")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
               'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # Report placeholders still on the site
    found = {}
    for f in sorted(DIST.rglob("*.html")):
        for m in PLACEHOLDER.findall(f.read_text(encoding="utf-8")):
            found.setdefault(m, set()).add(str(f.relative_to(DIST)))
    print(f"Built {'PRODUCTION' if production else 'preview (noindex)'} site in {DIST}")
    if found:
        print("\nPlaceholders still to fill in before go-live:")
        for text, files in found.items():
            print(f"  {text}  ({', '.join(sorted(files))})")
    checks = [a for a in site["airlines"] if a.get("_check")] + [m for m in site["team"] if m.get("_check")]
    if checks:
        print("\nOpen checks in content/site.json:")
        for c in checks:
            print(f"  {c.get('name', c.get('name_key'))}: {c['_check']}")


if __name__ == "__main__":
    main()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("\nServing http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
