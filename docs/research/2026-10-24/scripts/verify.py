"""Check publisher-deposited Crossref metadata for the manually screened shortlist."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
if ROOT.name == "scripts":
    ROOT = ROOT.parent


def doi_key(value):
    return value.lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def fetch(doi):
    cache = ROOT / "crossref" / (sha256(doi.encode()).hexdigest() + ".json")
    if cache.exists():
        return doi, json.loads(cache.read_text())
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Wildlitics-literature-check/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.load(response)["message"]
            result = {"retrieved_utc": datetime.now(timezone.utc).isoformat(), "url": url, "message": data}
            cache.write_text(json.dumps(result, ensure_ascii=False))
            return doi, result
        except Exception as exc:
            error = str(exc)
            time.sleep(1 + attempt)
    return doi, {"error": error, "url": url}


def choose_shortlist():
    if (ROOT / "selected-topics.json").exists():
        return json.loads((ROOT / "selected-topics.json").read_text())
    choices = json.loads((ROOT / "selection-draft.json").read_text())
    model_rows = json.loads((ROOT / "ml-title-candidates.json").read_text())
    excluded = {model_rows[i]["doi"] for i in [40,78,151,199,213,219,244,254,263,278]}
    model = [doi_key(x) for x in choices["model_candidates"] if x not in excluded]
    exclude_detection = {doi_key(model_rows[i]["doi"]) for i in [7,51,170,198,248,259,201,167,279]}
    detection = [doi for doi in model if doi not in exclude_detection]
    detection += [doi_key(model_rows[i]["doi"]) for i in [14,26,58,82,85,99,106,138,180]]
    analysis = [doi_key(x) for x in choices["analysis_candidates"]]
    analysis += [doi_key(model_rows[i]["doi"]) for i in [32,158,186,227]]
    analysis += ["10.1890/0012-9658(2002)083[2248:esorwd]2.0.co;2", "10.18637/jss.v043.i10", "10.1890/13-0133.1"]
    selection = {"model_enhancement": list(dict.fromkeys(model)),
                 "species_analysis": list(dict.fromkeys(analysis)),
                 "detection_accuracy_confusion": list(dict.fromkeys(detection))}
    return selection


def main():
    (ROOT / "crossref").mkdir(exist_ok=True)
    selection = choose_shortlist()
    (ROOT / "shortlist.json").write_text(json.dumps(selection, indent=2))
    all_dois = sorted({doi for values in selection.values() for doi in values})
    verified = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(fetch, doi) for doi in all_dois]):
            doi, record = future.result()
            verified[doi] = record
            if len(verified) % 20 == 0:
                print(f"{len(verified)}/{len(all_dois)} DOI records checked", flush=True)
    (ROOT / "verified-metadata.json").write_text(json.dumps(verified, ensure_ascii=False))
    candidate_path = ROOT / "candidates.json"
    candidates = {doi_key(x["doi"]):x for x in json.loads(candidate_path.read_text()) if x.get("doi")} if candidate_path.exists() else {}
    problems = []
    for doi, record in verified.items():
        item = record.get("message", {})
        title = re.sub('<[^>]+>', '', (item.get("title") or [""])[0])
        known = candidates.get(doi)
        similarity = None
        if known:
            normalize = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
            similarity = SequenceMatcher(None, normalize(known["title"]), normalize(title)).ratio()
        dates = {k:item[k].get("date-parts") for k in ["published", "published-online", "published-print", "issued"] if k in item}
        if record.get("error") or item.get("type") != "journal-article" or (similarity is not None and similarity < .9) or item.get("update-to"):
            problems.append({"doi":doi, "error":record.get("error"), "type":item.get("type"), "title":title,
                             "candidate_title":known.get("title") if known else None, "similarity":similarity,
                             "dates":dates, "update_to":item.get("update-to")})
    (ROOT / "metadata-problems.json").write_text(json.dumps(problems, indent=2, ensure_ascii=False))
    print(json.dumps({"topic_shortlists":{k:len(v) for k,v in selection.items()}, "unique":len(all_dois),"problems":problems}, indent=2), flush=True)


if __name__ == "__main__":
    main()
