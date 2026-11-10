#!/usr/bin/env python3
"""Render the CV site from content/cv.json and content/site.json.

Usage: python3 scripts/build.py

Writes index.html (EN), es/index.html, pt/index.html, 404.html and sitemap.xml.
Fails if any language is missing a string, so the three pages never drift apart.
Output depends only on the content files, so running it twice changes nothing.
"""
import html
import json
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("en", "es", "pt")
PATHS = {"en": "/", "es": "/es/", "pt": "/pt/"}
OUT = {"en": "index.html", "es": "es/index.html", "pt": "pt/index.html"}
OG_LOCALE = {"en": "en_US", "es": "es_CL", "pt": "pt_BR"}
LANG_NAMES = {"en": "English", "es": "Español", "pt": "Português"}

# Month names as the Living CV formats them, so dates match the exported PDFs.
MON = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
}

e = html.escape


def fail(msg):
    sys.exit(f"build: {msg}")


def check_parity(a, b, path):
    """Every language block in site.json must have the same shape as English."""
    if isinstance(a, dict):
        if not isinstance(b, dict):
            fail(f"{path} is not an object")
        missing = set(a) - set(b)
        extra = set(b) - set(a)
        if missing or extra:
            fail(f"{path}: missing {sorted(missing)} extra {sorted(extra)}")
        for k in a:
            check_parity(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            fail(f"{path} has a different number of items")
        for i, (x, y) in enumerate(zip(a, b)):
            check_parity(x, y, f"{path}[{i}]")
    elif isinstance(a, str):
        if not isinstance(b, str) or not b.strip():
            fail(f"{path} is empty")


def ym(value, lang, present):
    if not value:
        return present
    y, m = value.split("-")[:2]
    return f"{MON[lang][int(m) - 1]} {y}"


def day(value, lang):
    y, m, d = value.split("-")
    return f"{int(d)} {MON[lang][int(m) - 1]} {y}"


def ul(items, cls):
    lis = "".join(f"<li>{e(t)}</li>" for t in items)
    return f'<ul class="{cls}">{lis}</ul>'


def section(sid, heading, inner, extra_cls=""):
    cls = f"sec {extra_cls}".strip()
    hid = f"h-{sid}"
    return (
        f'<section class="{cls}" id="{sid}" aria-labelledby="{hid}">\n'
        f'  <h2 class="sec-h" id="{hid}">{e(heading)}</h2>\n'
        f'  <div class="sec-b">\n{inner}\n  </div>\n</section>'
    )


def email_link(profile, label, cls, show=False):
    user, domain = profile["email_user"], profile["email_domain"]
    attrs = f'class="{cls} js-email" href="#contact" data-u="{e(user)}" data-d="{e(domain)}"'
    if show:
        attrs += " data-show"
    return f"<a {attrs}>{e(label)}</a>"


def role_html(role, lang, s):
    title = e(role["title"][lang])
    dates = f'{e(ym(role["start"], lang, s["present"]))} – {e(ym(role["end"], lang, s["present"]))}'
    meta = f'<span class="co">{e(role["company"])}</span>'
    if role.get("note"):
        meta += f' <span class="note">({e(role["note"][lang])})</span>'
    if role.get("where"):
        meta += f' · {e(role["where"][lang])}'
    featured = [b[lang] for b in role["bullets"] if b["featured"]]
    rest = [b[lang] for b in role["bullets"] if not b["featured"]]
    if not featured:
        featured, rest = rest[:3], rest[3:]
    out = [
        f'<article class="role" id="role-{e(role["id"])}">',
        '  <div class="role-h">',
        f'    <h3 class="role-t">{title}</h3>',
        f'    <p class="role-d">{dates}</p>',
        "  </div>",
        f'  <p class="role-m">{meta}</p>',
        "  " + ul(featured, "bul"),
    ]
    if rest:
        more = e(s["show_more"].replace("{n}", str(len(rest))))
        out += [
            '  <details class="more">',
            f'    <summary><span class="m">{more}</span><span class="l">{e(s["show_less"])}</span></summary>',
            "    " + ul(rest, "bul"),
            "  </details>",
        ]
    out.append("</article>")
    return "\n".join(out)


def page_body(cv, site, lang):
    s = site[lang]
    shared = site["shared"]
    prof = cv["profile"]
    parts = []

    # Hero
    head_bits = [b.strip() for b in cv["headline"][lang].split("|") if b.strip()]
    role_line, facts = head_bits[0], head_bits[1:]
    # The CV button appears only once that language's PDF is in the repo.
    actions = [
        f'<a class="btn primary" href="/cv-{lang}.pdf" download>{e(s["cta_cv"])}</a>'
    ] if (ROOT / f"cv-{lang}.pdf").exists() else []
    actions += [
        f'<a class="btn" href="https://{e(prof["linkedin"])}" rel="me">LinkedIn</a>',
        f'<a class="btn" href="https://{e(prof["github"])}" rel="me">GitHub</a>',
        email_link(prof, s["email"], "btn"),
    ]
    parts.append(
        '<section class="hero" aria-labelledby="h-name">\n'
        f'  <h1 id="h-name">{e(prof["name"])}</h1>\n'
        f'  <p class="hero-role">{e(role_line)}</p>\n'
        + (f'  {ul(facts, "facts")}\n' if facts else "")
        + f'  <p class="hero-loc">{e(prof["location"][lang])}</p>\n'
        f'  <p class="hero-sum">{e(cv["summary"][lang])}</p>\n'
        f'  <div class="actions">{"".join(actions)}</div>\n'
        "</section>"
    )

    # Selected work
    cards = []
    for card in s["work"]:
        stack = shared["work_stack"].get(card["id"])
        if stack is None:
            fail(f"no work_stack for card '{card['id']}'")
        cards.append(
            '<article class="card">\n'
            '  <div class="card-h">\n'
            f'    <p class="kicker">{e(card["kicker"])}</p>\n'
            f'    <h3 class="card-t">{e(card["title"])}</h3>\n'
            "  </div>\n"
            '  <div class="card-b">\n'
            f'    {ul(card["points"], "bul")}\n'
            f'    {ul(stack, "chips")}\n'
            "  </div>\n"
            "</article>"
        )
    parts.append(section(
        "work", s["work_heading"],
        f'<p class="intro">{e(s["work_intro"])}</p>\n<div class="cards">\n' + "\n".join(cards) + "\n</div>",
    ))

    # Experience (+ earlier career), then entrepreneurship
    exp = [role_html(r, lang, s) for r in cv["roles"] if r["section"] == "experience"]
    if cv.get("earlier"):
        exp.append(
            '<div class="role earlier">\n'
            f'  <h3 class="role-t">{e(s["earlier"])}</h3>\n'
            f'  <p>{e(cv["earlier"][lang])}</p>\n'
            "</div>"
        )
    parts.append(section("experience", s["experience_heading"], '<div class="timeline">\n' + "\n".join(exp) + "\n</div>"))
    ven = [role_html(r, lang, s) for r in cv["roles"] if r["section"] == "venture"]
    if ven:
        parts.append(section("venture", s["venture_heading"], '<div class="timeline">\n' + "\n".join(ven) + "\n</div>"))

    # Skills
    rows = "\n".join(
        f'<div class="sk"><dt>{e(g["label"][lang])}</dt><dd>{ul(g["items"], "chips")}</dd></div>'
        for g in cv["skills"]
    )
    parts.append(section("skills", s["skills_heading"], f'<dl class="skills">\n{rows}\n</dl>'))

    # Certifications, education, languages
    certs = [c[lang] + (f" ({c['year']})" if c.get("year") else "") for c in cv["certs"]]
    parts.append(section("certs", s["certs_heading"], ul(certs, "list"), "compact"))
    edu = "\n".join(
        f'<li><span>{e(x[lang])}</span><span class="yr">{e(x.get("years", ""))}</span></li>' for x in cv["education"]
    )
    parts.append(section("education", s["edu_heading"], f'<ul class="list edu">\n{edu}\n</ul>', "compact"))
    parts.append(section("languages", s["langs_heading"], ul([x[lang] for x in cv["spoken"]], "inline"), "compact"))

    # Contact
    user, domain = prof["email_user"], prof["email_domain"]
    noscript = e(s["email_noscript"].replace("{user}", user).replace("{domain}", domain))
    contact = (
        f'<p class="intro">{e(s["contact_note"])}</p>\n'
        '<ul class="contact">\n'
        f'  <li><span class="ck">LinkedIn</span><a href="https://{e(prof["linkedin"])}" rel="me">{e(prof["linkedin"])}</a></li>\n'
        f'  <li><span class="ck">GitHub</span><a href="https://{e(prof["github"])}" rel="me">{e(prof["github"])}</a></li>\n'
        f'  <li><span class="ck">{e(s["email"])}</span>{email_link(prof, s["email"], "", show=True)}'
        f"<noscript>{noscript}</noscript></li>\n"
        "</ul>"
    )
    parts.append(section("contact", s["contact_heading"], contact))
    return "\n\n".join(parts)


def render(cv, site, lang, tpl):
    s = site[lang]
    base = site["shared"]["site_url"].rstrip("/")
    prof = cv["profile"]
    nav = "\n".join(
        f'      <a href="#{k}">{e(v)}</a>' for k, v in s["nav"].items()
    )
    langs = "\n".join(
        f'        <a href="{PATHS[l]}" hreflang="{l}" lang="{l}" title="{LANG_NAMES[l]}"'
        + (' aria-current="page"' if l == lang else "")
        + f">{l.upper()}</a>"
        for l in LANGS
    )
    alternates = "\n".join(
        [f'<link rel="alternate" hreflang="{l}" href="{base}{PATHS[l]}">' for l in LANGS]
        + [f'<link rel="alternate" hreflang="x-default" href="{base}/">']
    )
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Person",
        "name": prof["name"],
        "jobTitle": cv["headline"][lang].split("|")[0].strip(),
        "url": base + PATHS[lang],
        "sameAs": [f"https://{prof['linkedin']}", f"https://{prof['github']}"],
        "address": {"@type": "PostalAddress", "addressLocality": "Santiago", "addressCountry": "CL"},
    }, ensure_ascii=False)
    updated = cv.get("updated") or ""
    return tpl.substitute(
        lang=lang,
        title=e(s["html_title"]),
        description=e(s["meta_description"]),
        canonical=base + PATHS[lang],
        alternates=alternates,
        og_locale=OG_LOCALE[lang],
        jsonld=jsonld.replace("</", "<\\/"),
        skip=e(s["skip"]),
        home=PATHS[lang],
        name=e(prof["name"]),
        nav_label=e(s["nav_label"]),
        nav=nav,
        lang_label=e(s["lang_label"]),
        langs=langs,
        theme_to_dark=e(s["theme_to_dark"]),
        theme_to_light=e(s["theme_to_light"]),
        body=page_body(cv, site, lang),
        year=updated[:4],
        updated=e(s["updated"].replace("{date}", day(updated, lang))) if updated else "",
    )


def not_found(cv, site):
    links = " · ".join(f'<a href="{PATHS[l]}" lang="{l}">{e(site[l]["notfound_title"])}: {LANG_NAMES[l]}</a>' for l in LANGS)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>404 · {e(cv['profile']['name'])}</title>\n"
        '<meta name="robots" content="noindex">\n<meta name="color-scheme" content="light dark">\n'
        '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n'
        '<link rel="stylesheet" href="/assets/css/style.css">\n'
        '<script>try{var t=localStorage.getItem("theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>\n'
        "</head>\n<body>\n<main class=\"nf\" id=\"main\">\n"
        f"  <h1>404</h1>\n  <p>{links}</p>\n"
        "</main>\n</body>\n</html>\n"
    )


def sitemap(cv, site):
    base = site["shared"]["site_url"].rstrip("/")
    lastmod = cv.get("updated") or ""
    alts = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{base}{PATHS[l]}"/>' for l in LANGS
    )
    urls = "".join(
        f"\n  <url>\n    <loc>{base}{PATHS[l]}</loc>"
        + (f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else "")
        + alts
        + "\n  </url>"
        for l in LANGS
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        f"{urls}\n</urlset>\n"
    )


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != text:
        path.write_text(text, encoding="utf-8")
        print(f"wrote {rel}")


def main():
    cv = json.loads((ROOT / "content/cv.json").read_text(encoding="utf-8"))
    site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
    for lang in LANGS:
        if lang not in site:
            fail(f"site.json has no '{lang}' block")
        check_parity(site["en"], site[lang], lang)
    if "phone" in cv.get("profile", {}):
        fail("cv.json contains a phone number; run scripts/sanitize.py")

    tpl = Template((ROOT / "templates/page.html").read_text(encoding="utf-8"))
    for lang in LANGS:
        write(OUT[lang], render(cv, site, lang, tpl))
    write("404.html", not_found(cv, site))
    write("sitemap.xml", sitemap(cv, site))

    missing = [f"cv-{l}.pdf" for l in LANGS if not (ROOT / f"cv-{l}.pdf").exists()]
    if missing:
        print(f"note: no {', '.join(missing)} yet, so those pages have no Download CV button")


if __name__ == "__main__":
    main()
