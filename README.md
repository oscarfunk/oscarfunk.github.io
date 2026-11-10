# Óscar Castro · CV site

Source of [oscarfunk.github.io](https://oscarfunk.github.io): a static CV page in English, Spanish and Portuguese, served by GitHub Pages straight from `main`. Plain HTML/CSS/JS with no framework and no CI build.

## How it works

```
content/cv.json      CV content: a public-fields-only export of the Living CV master record
content/site.json    site copy per language (nav, headings, Selected work cards, contact note)
templates/page.html  page skeleton
scripts/sanitize.py  raw Living CV export -> content/cv.json (drops phone, notes, other versions)
scripts/build.py     content -> index.html, es/index.html, pt/index.html, 404.html, sitemap.xml
assets/              style.css, main.js, favicon.svg
cv-en.pdf, cv-es.pdf, cv-pt.pdf   downloadable CVs, exported from the Living CV
```

The generated HTML is committed. GitHub Pages serves the repo as is (`.nojekyll`).

## Updating

**From the Living CV (the usual path).** Edit the CV in the Living CV artifact, then ask Claude to "sync the CV site". Claude:

1. exports `resume/master` to a scratch folder
2. runs `python3 scripts/sanitize.py <export> > content/cv.json`
3. runs `python3 scripts/build.py`
4. shows the diff, then commits and pushes

The raw export never goes in the repo. It holds the phone number and private notes, and `.gitignore` blocks `master.json`.

`sanitize.py` warns when a bullet has no Spanish or Portuguese text and English is shown instead.

**By hand.** Edit `content/site.json` (or `content/cv.json`), then:

```sh
python3 scripts/build.py
git commit -am "Update CV" && git push
```

`build.py` stops if a language is missing a string, and running it twice changes nothing. The live site updates about a minute after a push.

**New PDFs.** Export EN, ES and PT from the Living CV and replace `cv-en.pdf`, `cv-es.pdf` and `cv-pt.pdf`.

## Preview locally

```sh
python3 -m http.server 8000
# open http://localhost:8000/ (and /es/, /pt/)
```
