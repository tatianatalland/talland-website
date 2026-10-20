#!/usr/bin/env python3
"""Bouwt de statische Talland-website.

Gebruik:  python3 src/build.py
Bron:     src/pages/*.html  (paginafragmenten met een kopblok)
          src/style.css, src/assets/*
Uitvoer:  docs/  (dit is wat GitHub Pages publiceert)

Wettelijke gegevens staan op ÉÉN plek: het blok BEDRIJF hieronder.
"""
import os, re, shutil, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "docs")
SITE_URL = "https://talland.be"

# ---------------------------------------------------------------------------
# Wettelijke gegevens (bron: FSMA-register + KBO). Wijzig alleen hier.
# ---------------------------------------------------------------------------
BEDRIJF = {
    "naam": "Talland BV",
    "handelsnaam": "Talland Insurance",
    "zetel": "Hemelrijk 98-100, 9402 Ninove",
    "kantoor_straat": "Leopoldlaan 210",
    "kantoor_gemeente": "9400 Ninove",
    "kbo": "0809.236.752",
    "fsma": "105113",
    "tel": "+32 477 65 72 14",
    "tel_href": "+32477657214",
    "mail": "info@talland.be",
    "statuten": "verzekeringsmakelaar (leven en niet-leven), makelaar in hypothecair krediet en makelaar in consumentenkrediet",
}

# Sleutel van de formulierdienst (web3forms.com). Leeg = formulieren tonen een melding.
WEB3FORMS_KEY = ""

# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
NAV = [
    ("Verzekeringen", "/verzekeringen/", [
        ("Particulier", "/verzekeringen/particulier/"),
        ("Zelfstandigen & KMO", "/verzekeringen/zelfstandigen-kmo/"),
    ]),
    ("Kredieten", "/krediet/", [
        ("Particulier", "/krediet/particulier/"),
        ("Zelfstandigen & KMO", "/krediet/kmo/"),
    ]),
    ("Over ons", "/over-ons/", []),
    ("Contact", "/contact/", []),
]

# Oude WordPress-adressen die niet meer bestaan -> nieuwe bestemming
REDIRECTS = {
    "/nieuws/": "/",
    "/nieuwsbrief/": "/contact/",
    "/mifid/": "/wettelijke-informatie/",
    "/login-customizer/": "/",
    "/offerte-aanvragen/": "/offerte-aanvraag/",
    "/2020/05/04/ook-vanuit-mijn-kot-ben-ik-er-voor-jou-2/": "/",
    "/2020/04/17/ook-vanuit-mijn-kot-ben-ik-er-voor-jou/": "/",
    "/2020/02/06/mijn-verzekeringsadvies-en-preventietips-2020/": "/",
    "/2019/07/01/mijn-verzekeringsadvies-en-preventietips-zomer/": "/",
    "/2019/02/19/mijn-verzekeringsadvies-en-preventietips/": "/",
    "/2019/02/15/op-wintersport-zonder-zorgen-nieuw-e-book/": "/",
    "/2017/01/24/website-online/": "/",
    "/2016/05/11/hypotheek/": "/krediet/particulier/hypothecair-krediet/",
}

# ---------------------------------------------------------------------------
def rel(target, page_path):
    """Maak een link relatief, zodat de site werkt op elk adres (ook het testadres)."""
    depth = len([p for p in page_path.strip("/").split("/") if p])
    prefix = "../" * depth if depth else "./"
    t = target.lstrip("/")
    return (prefix + t) if t else prefix

def fix_links(text, page_path):
    return re.sub(r'(href|src|action)="/(?!/)([^"]*)"',
                  lambda m: '%s="%s"' % (m.group(1), rel("/" + m.group(2), page_path)), text)

def read_page(fn):
    raw = open(fn, encoding="utf-8").read()
    m = re.match(r"\s*<!--(.*?)-->(.*)", raw, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    meta["body"] = m.group(2)
    return meta

def nav_html(current):
    items = []
    for label, href, sub in NAV:
        active = " active" if current.startswith(href) else ""
        if sub:
            subs = "".join('<li><a href="%s">%s</a></li>' % (h, l) for l, h in sub)
            items.append('<li class="has-sub%s"><a href="%s">%s</a><ul>%s</ul></li>' % (active, href, label, subs))
        else:
            items.append('<li class="%s"><a href="%s">%s</a></li>' % (active.strip(), href, label))
    return "".join(items)

def crumbs(path, titles):
    if path == "/":
        return ""
    parts = [p for p in path.strip("/").split("/") if p]
    out = ['<a href="/">Home</a>']
    for i in range(len(parts)):
        p = "/" + "/".join(parts[: i + 1]) + "/"
        t = html.escape(titles.get(p, parts[i].replace("-", " ").capitalize()))
        out.append(t if i == len(parts) - 1 else '<a href="%s">%s</a>' % (p, t))
    return '<nav class="crumbs" aria-label="Kruimelpad">' + ' <span>/</span> '.join(out) + "</nav>"

def footer():
    b = BEDRIJF
    return f"""
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <p class="f-brand">Talland</p>
      <p>{b['kantoor_straat']}<br>{b['kantoor_gemeente']}<br>
      <a href="tel:{b['tel_href']}">{b['tel']}</a><br>
      <a href="mailto:{b['mail']}">{b['mail']}</a><br>Op afspraak</p>
    </div>
    <div>
      <p class="f-head">Ga naar</p>
      <ul>
        <li><a href="/verzekeringen/">Verzekeringen</a></li>
        <li><a href="/krediet/">Kredieten</a></li>
        <li><a href="/over-ons/">Over ons</a></li>
        <li><a href="/offerte-aanvraag/">Offerte aanvragen</a></li>
        <li><a href="https://www.mysigura.be/" rel="noopener">Schade aangeven</a></li>
        <li><a href="https://portal.brokercloud.app/" rel="noopener">Klantenzone</a></li>
      </ul>
    </div>
    <div>
      <p class="f-head">Wettelijk</p>
      <ul>
        <li><a href="/wettelijke-informatie/">Wettelijke informatie</a></li>
        <li><a href="/klachten/">Klachten</a></li>
        <li><a href="/privacyverklaring/">Privacyverklaring</a></li>
        <li><a href="/cookie-policy/">Cookies</a></li>
        <li><a href="/a-i-verklaring/">AI-verklaring</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap legal">
    <p>{b['naam']}, handelend onder de naam {b['handelsnaam']} · Maatschappelijke zetel: {b['zetel']} ·
    Ondernemingsnummer {b['kbo']} · Ingeschreven bij de FSMA onder nummer {b['fsma']} als {b['statuten']} ·
    Toezicht: FSMA, Congresstraat 12-14, 1000 Brussel, <a href="https://www.fsma.be" rel="noopener">www.fsma.be</a> ·
    Klachten: <a href="/klachten/">Ombudsman van de Verzekeringen en Ombudsfin</a></p>
    <p>© {datetime.date.today().year} {b['naam']}</p>
  </div>
</footer>"""

def page_html(meta, titles):
    path = meta["path"]
    title = meta["title"]
    full_title = "Talland Insurance" if path == "/" else f"{title} | Talland Insurance"
    desc = html.escape(meta.get("description", ""))
    body = meta["body"].replace("{{WEB3FORMS_KEY}}", WEB3FORMS_KEY)
    for k, v in BEDRIJF.items():
        body = body.replace("{{%s}}" % k, v)
    if not WEB3FORMS_KEY:
        body = body.replace("<!--FORMNOTE-->", '<p class="note">Het formulier wordt binnenkort geactiveerd. Mail ons intussen op <a href="mailto:info@talland.be">info@talland.be</a>.</p>')
    hero = meta.get("hero", "")
    head_block = ""
    if meta.get("layout") != "home":
        lead = f'<p class="lead">{meta["lead"]}</p>' if meta.get("lead") else ""
        head_block = f'<header class="page-head"><div class="wrap">{crumbs(path, titles)}<h1>{html.escape(title)}</h1>{lead}</div></header>'
    doc = f"""<!doctype html>
<html lang="nl-BE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE_URL}{path}">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body class="{meta.get('layout','page')}">
<a class="skip" href="#inhoud">Naar de inhoud</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="/" aria-label="Talland Insurance, naar de startpagina"><span class="brand-mark">T</span><span class="brand-name">Talland<small>Insurance</small></span></a>
    <input type="checkbox" id="menu-toggle" class="menu-toggle" aria-label="Menu openen">
    <label for="menu-toggle" class="menu-btn"><span></span><span></span><span></span></label>
    <nav class="main-nav" aria-label="Hoofdmenu"><ul>{nav_html(path)}</ul>
      <a class="btn btn-small" href="/offerte-aanvraag/">Offerte aanvragen</a></nav>
  </div>
</header>
<main id="inhoud">
{head_block}
{body}
</main>
{footer()}
</body>
</html>
"""
    return fix_links(doc, path)

def redirect_html(old, new):
    target = rel(new, old)
    return f"""<!doctype html><html lang="nl-BE"><head><meta charset="utf-8">
<title>Deze pagina is verhuisd</title><meta name="robots" content="noindex">
<link rel="canonical" href="{SITE_URL}{new}"><meta http-equiv="refresh" content="0; url={target}">
</head><body><p>Deze pagina is verhuisd. <a href="{target}">Ga verder</a>.</p></body></html>"""

def write(path, content):
    out = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith(".html") else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(content)

def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    pages = [read_page(os.path.join(SRC, "pages", f)) for f in sorted(os.listdir(os.path.join(SRC, "pages"))) if f.endswith(".html")]
    titles = {p["path"]: p.get("crumb", p["title"]) for p in pages}
    for p in pages:
        write(p["path"], page_html(p, titles))
    for old, new in REDIRECTS.items():
        write(old, redirect_html(old, new))
    # 404 met absolute links (werkt op talland.be)
    nf = page_html({"path": "/404/", "title": "Pagina niet gevonden", "description": "",
                    "body": '<section class="wrap section"><p>Deze pagina bestaat niet (meer). <a href="/">Terug naar de startpagina</a>.</p></section>'}, titles)
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(nf.replace('href="../', 'href="/').replace('src="../', 'src="/'))
    shutil.copy(os.path.join(SRC, "style.css"), os.path.join(OUT, "assets", "style.css"))
    adir = os.path.join(SRC, "assets")
    if os.path.isdir(adir):
        for f in os.listdir(adir):
            shutil.copy(os.path.join(adir, f), os.path.join(OUT, "assets", f))
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    urls = "".join(f"<url><loc>{SITE_URL}{p['path']}</loc></url>" for p in pages)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(f"Klaar: {len(pages)} pagina's, {len(REDIRECTS)} doorverwijzingen -> docs/")

if __name__ == "__main__":
    main()
