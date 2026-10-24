"""Build the original research report and a searchable, offline bibliography."""
from collections import Counter
from datetime import date
from hashlib import sha256
import csv
import html
import json
from pathlib import Path
import re
import shutil
import unicodedata
from urllib.parse import quote
from zipfile import ZipFile, ZIP_DEFLATED

import markdown
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from curation import CORE, COMMUNITY, TECHNICAL

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT
if ROOT.name == "scripts":
    ROOT = ROOT.parent
OUT = ROOT / "output"
TOPICS = {"model_enhancement": "1. Enhancing identification models",
          "species_analysis": "2. Species data analysis and workflows",
          "detection_accuracy_confusion": "3. Detection, accuracy and confusion"}
FOCUS = [
 (r"calibrat|confidence|uncertaint", "Calibration and uncertainty", "Check calibration data, score meaning and behaviour on unseen sites."),
 (r"class imbalance|long.tail|rare species", "Class imbalance", "Check rare-class support, per-class precision/recall and the sampling strategy."),
 (r"generaliz|generalis|location|habitat|background|domain|transfer", "Transfer and generalisation", "Inspect camera/site holdouts, source domains and background leakage."),
 (r"sequence|temporal context|attention|motion vector", "Sequence context", "Check sequence units, mixed-species support and leakage between encounters."),
 (r"augment|copy.paste|synthetic", "Augmentation", "Check whether augmentation was applied after splitting and whether the holdout remained independent."),
 (r"active learning|human|citizen|expert|annotation|supervision", "Human review and labels", "Inspect reviewer agreement, label auditing and the effect on review effort."),
 (r"re.identif|individual|leopard|tiger", "Individual-ID / related task", "Separate individual recognition from species identification and check task-specific validation."),
 (r"occupancy|site.occup", "Occupancy", "Check repeated occasions, operational effort, closure, detection assumptions and model fit."),
 (r"activity|overlap|circadian|diel|independen", "Activity and time units", "Check circular estimators, sampling units, filter sensitivity and uncertainty."),
 (r"density|abundance|capture.recapture|encounter model|distance sampling", "Density and abundance", "Check estimator inputs, placement, detection geometry and individual-ID assumptions."),
 (r"diversity|richness|rarefaction|coverage|inext|accumulation", "Diversity and effort", "Check incidence versus abundance data, effort/completeness standardisation and uncertainty."),
 (r"data management|data exchange|camtrapr|camtrap dp|storage|warehouse|software|workflow|protocol|quality control", "Data workflow and quality", "Check interoperability, provenance, operating intervals and reproducibility."),
 (r"small|blur|infrared|night|illumination|nocturnal|camera.*model|obstruction|fast.moving", "Capture conditions and small animals", "Separate sensor detectability from algorithm recall; examine night/size/occlusion strata."),
 (r"detect|empty|blank|object|bounding|crop", "Detection and crops", "Check object recall, false positives, crop association and end-to-end species outcomes."),
 (r"classif|recogn|learning|neural|vision", "Identification models", "Check training/test separation, candidate classes, per-class results and local transferability."),
]


def clean(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", "", str(value))).split())


def first_date(item):
    dates = []
    for field in ("published-online", "published", "published-print", "issued"):
        for parts in item.get(field, {}).get("date-parts", []):
            if parts:
                dates.append(date(*(parts + [1, 1])[:3]))
    return min(dates).isoformat() if dates else None


def citation_year(item):
    for field in ("published-print", "published", "published-online", "issued"):
        parts = item.get(field, {}).get("date-parts", [[]])[0]
        if parts and parts[0] <= 2026:
            return parts[0]
    raise ValueError("No eligible citation year")


def csv_file(path, records, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: "; ".join(record[key]) if isinstance(record.get(key), list)
                             else record.get(key, "") for key in fields})


def build_library():
    selected = json.loads((ROOT / "selected-topics.json").read_text())
    metadata = json.loads((ROOT / "verified-metadata.json").read_text())
    candidate_path = ROOT / "candidates.json"
    candidates = {x["doi"].lower().removeprefix("https://doi.org/"):x
                  for x in json.loads(candidate_path.read_text()) if x.get("doi")} if candidate_path.exists() else {}
    core = {x[0]: {"focus": x[1], "finding": x[2], "limit": x[3], "action": x[4]} for x in CORE}
    library = []
    for doi in sorted({doi for values in selected.values() for doi in values}):
        result = metadata[doi]
        item = result["message"]
        assert item["type"] == "journal-article" and not result.get("error")
        published = first_date(item)
        date_basis = "Earliest date deposited in the checked Crossref record; earlier online releases may be omitted"
        if doi == "10.1016/j.scitotenv.2026.181926":
            published = "2026-06-04"
            date_basis = "PubMed PMID 42241933 Epub date, checked 24 October 2026; Crossref lists the August issue"
        assert published and published <= "2026-10-24"
        title = clean(item["title"][0])
        journal = clean(item["container-title"][0])
        authors = [clean(" ".join([a.get("given", ""), a.get("family", a.get("name", ""))]))
                   for a in item.get("author", [])]
        assert title and journal and authors
        subjects = [(tag, question) for pattern, tag, question in FOCUS if re.search(pattern, title, re.I)]
        if not subjects:
            subjects = [("Survey design", "Inspect the survey objective, data requirements and applicability to camera-trap projects.")]
        if doi in core:
            subjects.insert(0, (core[doi]["focus"], core[doi]["action"]))
        original = candidates.get(doi, {})
        library.append({
            "id": "WL-" + sha256(doi.encode()).hexdigest()[:8].upper(), "doi": doi,
            "url": "https://doi.org/" + quote(doi, safe="/.:;()"),
            "title": title, "authors": authors, "year": citation_year(item), "first_publication_date": published,
            "publication_date_basis": date_basis,
            "journal": journal, "publisher": clean(item.get("publisher", "")),
            "volume": item.get("volume", ""), "issue": item.get("issue", ""),
            "pages_or_article": item.get("page", item.get("article-number", "")),
            "topics": [key for key, values in selected.items() if doi in values],
            "focus_tags": list(dict.fromkeys(tag for tag, _ in subjects))[:5],
            "reading_question": subjects[0][1],
            "assessment_level": "priority_source_assessment" if doi in core else "title_and_metadata_screened",
            "evidence_note": core.get(doi),
            "crossref_type": item["type"], "metadata_verified_utc": result["retrieved_utc"],
            "crossref_api_url": result["url"], "crossref_record_sha256": sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "update_notices_in_record": item.get("update-to", []),
            "openalex_id": original.get("id"), "openalex_retracted_flag": original.get("is_retracted"),
            "open_access_index_status": original.get("open_access", {}).get("oa_status", "not_retrieved"),
            "abstract_present_in_discovery_metadata": bool(original.get("abstract_inverted_index")),
        })
    library.sort(key=lambda x: (x["assessment_level"] != "priority_source_assessment", -x["year"], x["title"]))
    assert len(library) == 200 and all(sum(key in r["topics"] for r in library) == 100 for key in TOPICS)
    titles = [re.sub(r"\W", "", unicodedata.normalize("NFKD", x["title"]).casefold()) for x in library]
    assert len(set(titles)) == len(titles), "Duplicate normalised article titles"
    assert len(core) == 28 and set(core) <= {x["doi"] for x in library}
    return library, selected


def write_texts(library, selected):
    shutil.copyfile(ROOT / "REPORT.md", OUT / "REPORT.md")
    by_doi = {x["doi"]:x for x in library}
    core_md = ["# Priority evidence and its limits", "", "28 sources assessed through abstracts, accessible article sections or author/publisher method content. These notes distinguish reported findings from proposed Wildlitics changes. No performance number is a local Wildlitics result.", ""]
    for n, (doi, focus, finding, limit, action) in enumerate(CORE, 1):
        r = by_doi[doi]
        core_md += [f"## {n}. {focus}", "", f"**{r['title']}**. {r['journal']}, {r['year']}. [DOI]({r['url']})", "",
                    f"**Reported evidence:** {finding}", "", f"**Limit:** {limit}", "", f"**Wildlitics proposal:** {action}", ""]
    (OUT / "KEY_EVIDENCE.md").write_text("\n".join(core_md))
    for key, name in TOPICS.items():
        rows = sorted([x for x in library if key in x["topics"]], key=lambda x: (-x["year"], x["title"]))
        content = [f"# {name}", "", "100 journal articles. Overlap with other topic lists is intentional. First-online and issue years can differ; see the CSV/JSON date fields. 'Reading question' is a relevance prompt, not an unverified result.", ""]
        for n, r in enumerate(rows, 1):
            author = r["authors"][0] + (" et al." if len(r["authors"]) > 1 else "")
            content += [f"{n}. **{r['title']}** — {author} ({r['year']}). *{r['journal']}*. [DOI]({r['url']}). ID: {r['id']}. Assessment: {r['assessment_level']}.",
                        f"   Reading question: {r['reading_question']}", ""]
        (OUT / (key + ".md")).write_text("\n".join(content))
        csv_file(OUT / (key + ".csv"), rows, ["id", "title", "authors", "year", "first_publication_date", "publication_date_basis", "journal", "doi", "url", "focus_tags", "assessment_level", "reading_question"])
    community = ["# WILDLABS and technical discussion watch", "", "Checked 24 October 2026. These are community/vendor/project reports, distinct from peer-reviewed evidence. No posts or messages were sent. Dates refer to the named post rather than proof of the last software release.", ""]
    for r in sorted(COMMUNITY, key=lambda x:x["date"], reverse=True):
        community += [f"## {r['date']} — {r['title']}", "", f"Source: {r['source']}. [Read post]({r['url']}).", "", f"**Evidence type:** {r['evidence_type']}.", "",
                      f"**Reported:** {r['reported']}", "", f"**Wildlitics proposal:** {r['wildlitics_action']}", "", f"**Priority:** {r['priority']}.", ""]
    community += ["## Official documentation and additional foundations", "", "The references below are outside the journal quota. Their inclusion is not a claim that their code or models have been integrated.", ""]
    for r in TECHNICAL:
        community += [f"- [{r['title']}]({r['url']}) — {r['type']}. {r['use']}", ""]
    (OUT / "COMMUNITY_UPDATES.md").write_text("\n".join(community))
    (OUT / "community-updates.json").write_text(json.dumps({"items":COMMUNITY,"technical_references":TECHNICAL},ensure_ascii=False,indent=2))
    csv_file(OUT / "community-updates.csv", COMMUNITY, list(COMMUNITY[0]))


def write_methodology(library):
    audit = json.loads((ROOT / "search-audit.json").read_text())
    text = """# Search and verification method

Cutoff and retrieval date: 24 October 2026. Purpose: a practical evidence map and development review for Wildlitics.

## Discovery

48 targeted OpenAlex searches returned 1,270 distinct indexed candidate records (deduplicated by DOI or OpenAlex ID); three foundational DOIs were also added directly. Each search requested up to 60 ranked records, with article/journal, non-retracted and publication-date filters. Query strings, API URLs and returned counts are in search-audit.json. Web searches additionally located primary papers, author resources and community discussions.

Searches were organised around model enhancement; ecological analysis; and detection/accuracy/confusion. Search-result membership alone was not used as proof of topical relevance. Shortlisted titles were inspected for relevant tasks, recognised journal venues and a usable DOI. General medical/microbiome, unrelated engineering, theses, broad student demonstrations, conference abstracts, preprint-only and no-DOI discovery results were not included in the journal quota. Related camera-trap taxa and individual-ID papers are marked by focus tags; they are not all direct tests of Bornean species recognition.

223 unique shortlisted DOI records were checked against Crossref. The final topic selections contain 200 unique articles, each with matching journal-article metadata. Citation years use issue/print years where available; first publication dates are stored separately. This explains entries such as the calibration paper first online in 2024 but in a 2025 issue, and the independence-filter counter-study first online in December 2024 but in a 2025 issue.

## Verification scope

For every included record: Crossref returned the DOI, title, journal, authors and a publication date; the record type was journal-article; an available publication date was on or before the cutoff. The first-publication field normally records the earliest date deposited in Crossref, which can omit an earlier online release. The SpeciesNet fine-tuning paper uses the earlier PubMed Epub date with its basis recorded explicitly. OpenAlex and Crossref titles were compared where both were present. DOI, normalised-title and within-topic duplicates were checked. No update-to notice was present in these included Crossref records and no retraction was flagged in the available OpenAlex records. These metadata checks are not a comprehensive assessment of research integrity, peer-review quality or all post-publication notices.

All final entries received title/metadata screening. 28 priority sources received closer abstract, accessible-section or author/publisher method assessment; their findings, limits and proposals are in KEY_EVIDENCE.md. Other library rows have reading questions, not asserted study conclusions. The pipeline does not pretend an abstract was read just because it was retrieved. No full abstracts or papers are redistributed.

100 articles appear in each topic list. There are 300 topic placements and 200 unique papers; overlap is explicit. Lists include methods, reviews, software-method articles and relevant empirical applications. The article type alone does not guarantee quality, and citation counts were not used as a performance or quality score.

## Limits

This is a targeted review, not a registered systematic review or meta-analysis. The 60-result cap and search terms can miss relevant work; the OpenAlex article filter can omit separately indexed reviews. English-language discovery and available metadata influence coverage. Not all linked publisher pages or full texts were accessible or opened. Bibliographic verification is separate from assessing a study's methods and validity. No pooled performance estimate, universal training-set size or guaranteed Wildlitics improvement is calculated.

WILDLABS.net is the conservation technology site used here (the requested wildlibs.com was interpreted from the established conversation context). Ten dated community items and eleven technical references are separated from journal evidence. Community/vendor claims are not independently reproduced results. The search is a dated snapshot, not a scheduled monitoring service.

## Reproducibility and files

literature.json and literature.csv contain the final records, topic memberships, reading questions, review level, verification dates, Crossref API URLs and SHA-256 fingerprints of the metadata records checked. library.ris supports reference-manager import. selected-topics.json fixes the DOI membership of each list; search-audit.json preserves discovery requests. The build and discovery scripts are included under scripts, alongside the original synthesis notes. Raw API responses containing abstracts are kept outside the shared package.

The report contains original paraphrases and application proposals with linked sources. It does not adopt a new licence for Wildlitics, copy third-party application code, update the installed app, or validate field accuracy.

To rebuild after extracting the package: install scripts/requirements.txt, run python scripts/verify.py to fetch metadata for the frozen DOI selections, then python scripts/build.py. The build writes a new output directory and ZIP. Discovery can be repeated separately with python scripts/collect.py; its new rankings do not automatically change the curated selections. Exact original metadata snapshots can change upstream, so fingerprints may differ in a later rebuild. Fonts for PDF output use the standard Linux DejaVu Sans paths in the build script; adjust those paths on other platforms.

## Exact discovery queries

"""
    for topic in TOPICS:
        text += "\n### " + TOPICS[topic] + "\n\n"
        for a in audit:
            if a["topic"] == topic:
                text += "- " + a["query"] + "\n"
    (OUT / "METHODOLOGY.md").write_text(text)
    shutil.copyfile(ROOT / "search-audit.json", OUT / "search-audit.json")
    shutil.copyfile(ROOT / "selected-topics.json", OUT / "selected-topics.json")


def write_ris(library):
    lines=[]
    for r in library:
        lines += ["TY  - JOUR", "ID  - " + r["id"], "TI  - " + r["title"]]
        lines += ["AU  - " + a for a in r["authors"]]
        lines += ["PY  - " + str(r["year"]), "JO  - " + r["journal"], "DO  - " + r["doi"], "UR  - " + r["url"]]
        if r["volume"]:lines.append("VL  - " + str(r["volume"]))
        if r["issue"]:lines.append("IS  - " + str(r["issue"]))
        lines += ["KW  - " + TOPICS[t] for t in r["topics"]]
        lines += ["N1  - Assessment: " + r["assessment_level"], "ER  - ", ""]
    (OUT / "library.ris").write_text("\n".join(lines))


def write_html(library):
    payload=json.dumps(library,ensure_ascii=False).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    md=lambda name:markdown.markdown((OUT/name).read_text(),extensions=["tables"])
    options=''.join(f'<option value="{k}">{html.escape(v)}</option>' for k,v in TOPICS.items())
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wildlitics research library — 24 October 2026</title><style>
:root{font-family:system-ui,sans-serif;color:#172e2c;background:#f4f7f4;line-height:1.55}body{max-width:1200px;margin:0 auto;padding:24px}header{background:#173f39;color:#fff;padding:30px;border-radius:14px}h1{font-size:2rem;line-height:1.2}h2{margin-top:1.5em}a{color:#17675c}header a{color:#d8f2d9}nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}button,select,input{font:inherit;padding:10px;border:1px solid #a7b8b0;border-radius:7px;background:white}button{cursor:pointer}button[aria-pressed="true"]{background:#173f39;color:white}section{background:white;padding:24px;border-radius:12px;margin-top:15px}.metrics{display:flex;gap:20px;flex-wrap:wrap}.metrics b{font-size:2rem;display:block}.filters{display:flex;gap:8px;flex-wrap:wrap;position:sticky;top:0;background:#edf4ef;padding:12px;z-index:1}#search{flex:2;min-width:220px}article{padding:18px 0;border-top:1px solid #dbe5dd}article h3{margin:0 0 5px;font-size:1.1rem}.muted{color:#52675d}.tag{display:inline-block;background:#edf3e9;border-radius:4px;padding:1px 6px;margin:3px;font-size:.8rem}.core{border-left:4px solid #548265;padding-left:12px}table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{border:1px solid #dbe5dd;text-align:left;padding:8px;vertical-align:top}[hidden]{display:none!important}summary{cursor:pointer}footer{margin-top:25px}.notice{background:#f4f0df;padding:12px;border-radius:7px}@media print{nav,.filters,button{display:none}body{padding:0;background:white}section{padding:0}a{color:inherit}header{background:white;color:#172e2c}}</style>
<header><p>WILDLITICS / RESEARCH SNAPSHOT / 24 OCTOBER 2026</p><h1>Evidence for the next Wildlitics improvements</h1><div class="metrics"><div><b>200</b>unique journal articles</div><div><b>100 × 3</b>topic placements, with overlap</div><div><b>28</b>priority source assessments</div><div><b>10</b>community updates</div></div><p>Local validation, clean survey data and reproducible analysis come first.</p></header>
<nav aria-label="Report sections"><button data-view="overview" aria-pressed="true">Development summary</button><button data-view="library" aria-pressed="false">Search papers</button><button data-view="evidence" aria-pressed="false">Key evidence</button><button data-view="updates" aria-pressed="false">WILDLABS & software</button><button data-view="methods" aria-pressed="false">Method & limits</button></nav>
<section id="overview">OVERVIEW<p><a href="Wildlitics-research-review.pdf">Download PDF review</a> · <a href="literature.csv">CSV</a> · <a href="library.ris">RIS / Zotero</a></p></section>
<section id="library" hidden><h2>Search the journal library</h2><p class="notice">Metadata verification establishes the bibliographic record. 28 priority sources have synthesis notes; other records have title-based reading questions. Software and preprints are in the separate updates section.</p><div class="filters"><input id="search" aria-label="Search papers" placeholder="Search title, author, journal, DOI, or focus"><select id="topic" aria-label="Topic"><option value="">All topics</option>OPTIONS</select><select id="level" aria-label="Assessment level"><option value="">All assessment levels</option><option value="priority_source_assessment">28 priority assessments</option><option value="title_and_metadata_screened">Title & metadata only</option></select><select id="year" aria-label="Publication year"><option value="">All years</option><option value="2026">2026</option><option value="2025">2025</option><option value="2024">2024</option><option value="recent">2024–2026</option></select></div><p id="count" role="status"></p><div id="papers"></div><noscript>JavaScript is needed for filtering; use the CSV or topic Markdown lists without it.</noscript></section>
<section id="evidence" hidden>EVIDENCE</section><section id="updates" hidden>UPDATES</section><section id="methods" hidden>METHODS</section><footer class="muted">Offline report: filtering uses only embedded bibliography data. External links open the source sites. No research photographs, sensitive coordinates, model weights or copied article abstracts are included.</footer>
<script type="application/json" id="data">PAYLOAD</script><script>
const papers=JSON.parse(document.getElementById('data').textContent), titles=TOPICJSON;
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function render(){const query=document.getElementById('search').value.toLowerCase(),topic=document.getElementById('topic').value,level=document.getElementById('level').value,year=document.getElementById('year').value;
 const rows=papers.filter(p=>(!topic||p.topics.includes(topic))&&(!level||p.assessment_level===level)&&(!year||(year==='recent'?p.year>=2024:p.year===Number(year)))&&[p.title,p.authors.join(' '),p.journal,p.doi,p.focus_tags.join(' ')].join(' ').toLowerCase().includes(query));
 const target=document.getElementById('papers');target.replaceChildren();document.getElementById('count').textContent=rows.length+' unique papers shown';
 for(const p of rows){const a=node('article');if(p.evidence_note)a.className='core';const h=node('h3');const link=node('a',p.title);link.href=p.url;link.target='_blank';link.rel='noopener noreferrer';h.append(link);a.append(h,node('div',p.authors.slice(0,3).join('; ')+(p.authors.length>3?' et al.':'')+' · '+p.journal+' · '+p.year,'muted'),node('div',p.id+' · '+p.doi,'muted'));const tags=node('div');for(const t of p.topics)tags.append(node('span',titles[t],'tag'));for(const t of p.focus_tags)tags.append(node('span',t,'tag'));a.append(tags);a.append(node('p',p.evidence_note?'Reported evidence: '+p.evidence_note.finding:'Reading question: '+p.reading_question));if(p.evidence_note){a.append(node('p','Limit: '+p.evidence_note.limit),node('p','Wildlitics proposal: '+p.evidence_note.action));}const d=node('details');d.append(node('summary','Assessment and bibliographic verification'),node('p','Assessment: '+p.assessment_level+'. First publication: '+p.first_publication_date+'. Crossref verified: '+p.metadata_verified_utc+'. Published record type: '+p.crossref_type+'. Open access index status: '+p.open_access_index_status+'.'));a.append(d);target.append(a);}}
document.querySelectorAll('button[data-view]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('button[data-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('section').forEach(s=>s.hidden=s.id!==b.dataset.view);if(b.dataset.view==='library')render();}));
['search','topic','level','year'].forEach(id=>document.getElementById(id).addEventListener(id==='search'?'input':'change',render));render();
</script></html>'''
    for old,new in [('OVERVIEW',md('REPORT.md')),('EVIDENCE',md('KEY_EVIDENCE.md')),('UPDATES',md('COMMUNITY_UPDATES.md')),('METHODS',md('METHODOLOGY.md')),('OPTIONS',options),('PAYLOAD',payload),('TOPICJSON',json.dumps(TOPICS))]:
        page=page.replace(old,new)
    (OUT/'index.html').write_text(page)


def write_pdf():
    pdfmetrics.registerFont(TTFont('Research','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('ResearchBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFontFamily('Research',normal='Research',bold='ResearchBold',italic='Research',boldItalic='ResearchBold')
    styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName='Research'
    styles['Normal'].fontSize=9;styles['Normal'].leading=14;styles['Normal'].spaceAfter=8
    styles['Heading1'].fontSize=19;styles['Heading1'].leading=24
    styles['Heading2'].fontSize=13;styles['Heading2'].leading=18
    styles['Heading3'].fontSize=11;styles['Heading3'].leading=15
    small=ParagraphStyle('Small',parent=styles['Normal'],fontSize=8,leading=11)
    def inline(value):
        s=markdown.markdown('WLINLINE ' + value)
        s=re.sub(r'^<p>|</p>$','',s)
        s=s.removeprefix('WLINLINE ')
        s=re.sub(r'<code>(.*?)</code>',r'<b>\1</b>',s)
        # ReportLab accepts link tags but relative companion files are not PDF destinations.
        return re.sub(r'<a href="(?!https?://)[^"]*">(.*?)</a>',r'\1',s)
    story=[]
    for file_n,filename in enumerate(['REPORT.md','KEY_EVIDENCE.md']):
        if file_n:story.append(PageBreak())
        lines=(OUT/filename).read_text().splitlines();i=0
        while i<len(lines):
            line=lines[i]
            if not line.strip():i+=1;continue
            if line.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].startswith('|'):
                    parts=[x.strip() for x in lines[i].strip('|').split('|')]
                    if not all(re.fullmatch(r'[-: ]+',x) for x in parts):rows.append([Paragraph(inline(x),small)for x in parts])
                    i+=1
                widths=[365,146] if len(rows[0])==2 else [40,220,251]
                table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eee7')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b8c6bc')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
                story.extend([table,Spacer(1,12)]);continue
            match=re.match(r'^(#{1,3}) (.*)',line)
            if match:
                story.append(Paragraph(inline(match[2]),styles['Heading'+str(len(match[1]))]));i+=1;continue
            paragraph=[line];i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')):
                paragraph.append(lines[i]);i+=1
            story.append(Paragraph(inline(' '.join(paragraph)),styles['Normal']))
    def foot(canvas,doc):
        canvas.saveState();canvas.setFont('Research',8);canvas.setFillColor(colors.HexColor('#52675d'))
        canvas.drawString(42,26,'Wildlitics research review | 24 October 2026');canvas.drawRightString(A4[0]-42,26,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(OUT/'Wildlitics-research-review.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42,title='Wildlitics research review and development priorities',author='Prepared for Brian Martin')
    doc.build(story,onFirstPage=foot,onLaterPages=foot)


def main():
    OUT.mkdir(exist_ok=True)
    library,selected=build_library()
    (OUT/'literature.json').write_text(json.dumps(library,ensure_ascii=False,indent=2))
    csv_file(OUT/'literature.csv',library,['id','title','authors','year','first_publication_date','publication_date_basis','journal','doi','url','topics','focus_tags','assessment_level','reading_question','crossref_type','metadata_verified_utc','crossref_api_url','crossref_record_sha256','open_access_index_status'])
    write_texts(library,selected);write_methodology(library);write_ris(library);write_html(library);write_pdf()
    (OUT/'scripts').mkdir(exist_ok=True)
    for name in ['collect.py','verify.py','build.py','curation.py']:
        shutil.copyfile(SOURCE/name,OUT/'scripts'/name)
    (OUT/'scripts'/'requirements.txt').write_text('Markdown==3.11.2\nreportlab==4.4.9\n')
    readme='''# Wildlitics research package

Start with **index.html** for the offline, searchable report and library, or **Wildlitics-research-review.pdf** for the narrative review and 28 evidence notes.

- 100 journal articles per requested topic; 200 unique papers, with overlap explicitly recorded.
- All included DOI records checked against Crossref metadata. Title/metadata screening is distinguished from 28 closer priority-source assessments.
- literature.csv / literature.json: complete bibliography and verification fields.
- library.ris: import into Zotero or another reference manager.
- model_enhancement, species_analysis, detection_accuracy_confusion: three 100-paper lists in Markdown and CSV.
- COMMUNITY_UPDATES.md: 10 dated discussion/news items and 11 additional technical/foundation references.
- METHODOLOGY.md: search process, exact queries, limits and interpretation of counts.
- scripts: discovery, verification, curation and report-building source.

The PDF has the narrative and priority evidence; the full 200-reference library is in the HTML/CSV/RIS and topic lists. Filtering works offline; opening source links needs internet. The public GitHub version may omit the generated PDF, which is included in the downloadable package.

This is a research deliverable. No installed Wildlitics application code, weights, photos or sensitive study locations are included or modified. No paper's performance result is a measured result for Wildlitics.
'''
    (OUT/'README.md').write_text(readme)
    counts={key:sum(key in x['topics'] for x in library)for key in TOPICS}
    status={'cutoff':'2026-10-24','unique_journal_articles':len(library),'topic_counts':counts,'total_topic_placements':sum(counts.values()),'priority_source_assessments':len(CORE),'community_items':len(COMMUNITY),'additional_technical_references':len(TECHNICAL),'crossref_metadata_checks_passed':len(library),'duplicates_by_doi':0,'duplicates_by_normalised_title':0,'future_publications':0,'all_papers_read_full_text':False,'systematic_review':False,'field_accuracy_measured':False,'application_code_changed':False}
    (OUT/'validation.json').write_text(json.dumps(status,indent=2))
    archive=ROOT/'wildlitics-research-2026-10-24.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED)as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():z.write(path,arcname='wildlitics-research-2026-10-24/'+str(path.relative_to(OUT)))
    print(json.dumps({**status,'zip':str(archive),'zip_bytes':archive.stat().st_size},indent=2))


if __name__=='__main__':main()
