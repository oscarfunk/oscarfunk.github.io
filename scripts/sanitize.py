#!/usr/bin/env python3
"""Turn a raw Living CV master record into content/cv.json, keeping only public fields.

Usage: python3 scripts/sanitize.py path/to/master.json > content/cv.json

The raw record holds things that must never be published: the phone number, the
private `todo` list, other tailored versions and their `purpose` notes, and
bullet tags. This script copies an explicit allow-list of fields and nothing else.

Bullet selection follows the Living CV's own logic for the chosen version
(default "lead"): a bullet's rank is the position of its best tag in the
version's tag list, and the top `limits[role]` ranked bullets are "featured".
The site shows featured bullets first and the rest behind "Show more".
"""
import json
import sys

LANGS = ("en", "es", "pt")
VERSION = "lead"
DEFAULT_LIMIT = 4


def loc(obj, field):
    """Pick en/es/pt from a localized object, falling back to English like the Living CV does."""
    if obj is None:
        return None
    if isinstance(obj, str):
        return {lang: obj for lang in LANGS}
    out = {}
    for lang in LANGS:
        val = obj.get(lang)
        if not val:
            val = obj.get("en") or ""
            if not val:
                sys.exit(f"sanitize: {field} has no '{lang}' or 'en' text")
            FALLBACKS.append(f"{field} [{lang}]")
        out[lang] = val
    return out


FALLBACKS = []


def rank(bullet, tags):
    best = 99
    for tag in bullet.get("tags") or []:
        if tag in tags:
            best = min(best, tags.index(tag))
    return best


def main(path):
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    master = raw.get("data", raw)

    versions = {v["id"]: v for v in master["versions"]}
    if VERSION not in versions:
        sys.exit(f"sanitize: version '{VERSION}' not found")
    ver = versions[VERSION]
    vtags = ver.get("tags") or []
    limits = ver.get("limits") or {}

    prof = master["profile"]
    profile = {
        "name": prof["name"],
        "location": loc(prof.get("location"), "profile.location"),
        # Split so the address never appears whole in the public repo.
        "email_user": prof["email"].split("@")[0],
        "email_domain": prof["email"].split("@")[1],
        "linkedin": prof["linkedin"],
        "github": prof["github"],
    }

    roles = []
    for role in master["roles"]:
        rid = role["id"]
        limit = limits.get(rid, DEFAULT_LIMIT)
        ranked = [
            (rank(b, vtags), i, b.get("id") or f"{rid}-{i + 1}")
            for i, b in enumerate(role["bullets"])
        ]
        auto = sorted((r for r in ranked if r[0] < 99), key=lambda r: (r[0], r[1]))
        featured = {r[2] for r in auto[:limit]}
        bullets = []
        for i, b in enumerate(role["bullets"]):
            bid = b.get("id") or f"{rid}-{i + 1}"
            item = {"id": bid, "featured": bid in featured}
            item.update(loc(b, f"roles.{rid}.{bid}"))
            bullets.append(item)
        roles.append({
            "id": rid,
            "section": role.get("section", "experience"),
            "company": role["company"],
            "title": loc(role["title"], f"roles.{rid}.title"),
            "note": loc(role.get("note"), f"roles.{rid}.note"),
            "where": loc(role.get("where"), f"roles.{rid}.where"),
            "start": role.get("start"),
            "end": role.get("end"),
            "bullets": bullets,
        })

    skill_order = list(ver.get("skills") or [])
    skill_order += [k for k in master["skills"] if k not in skill_order]
    skills = []
    for key in skill_order:
        group = master["skills"].get(key)
        if not group:
            continue
        label = loc(group, f"skills.{key}")
        skills.append({"id": key, "label": label, "items": list(group["items"])})

    def with_year(item, field, year_key):
        out = loc(item, field)
        out[year_key] = item.get(year_key, "")
        return out

    cv = {
        "updated": master.get("updated", ""),
        "version": VERSION,
        "profile": profile,
        "headline": loc(ver["title"], f"versions.{VERSION}.title"),
        "summary": loc(ver["summary"], f"versions.{VERSION}.summary"),
        "roles": roles,
        "earlier": loc(master.get("earlier"), "earlier"),
        "skills": skills,
        "education": [with_year(e, "education", "years") for e in master.get("education", [])],
        "certs": [with_year(c, "certs", "year") for c in master.get("certs", [])],
        "spoken": [loc(s, "spoken") for s in master.get("spoken", [])],
    }
    json.dump(cv, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    if FALLBACKS:
        sys.stderr.write(
            "sanitize: warning: no translation, showing English instead:\n  "
            + "\n  ".join(FALLBACKS)
            + "\nAdd the missing text in the Living CV and sync again.\n"
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
