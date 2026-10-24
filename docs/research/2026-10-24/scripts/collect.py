"""Reproducible bibliographic discovery, not an automated claim of paper review."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
if ROOT.name == "scripts":
    ROOT = ROOT.parent
QUERIES = {
    "model_enhancement": [
        "camera trap deep learning", "camera trap transfer learning", "camera trap species classification",
        "camera trap foundation models", "camera trap vision transformer", "camera trap self supervised",
        "camera trap fine tuning", "camera trap active learning", "camera trap semi supervised",
        "camera trap domain adaptation", "camera trap few shot learning", "camera trap ensemble learning",
        "wildlife image classification deep learning", "camera trap synthetic data augmentation",
        "camera trap continual learning", "camera trap feature extraction",
    ],
    "species_analysis": [
        "camera trap occupancy detection probability", "camera trap activity overlap",
        "camera trap density random encounter", "camera trap species richness sampling",
        "camera trap data management software", "camera trap spatial capture recapture",
        "camera trap detection rate abundance", "camera trap sampling design effort",
        "camera trap false positive occupancy", "camera trap independent events",
        "camera trap biodiversity community monitoring", "camera trap circular activity estimation",
        "camera trap metadata data standard", "camera trap distance sampling",
        "occupancy models imperfect detection", "species richness sample coverage rarefaction",
    ],
    "detection_accuracy_confusion": [
        "camera trap animal detection", "camera trap object detection", "camera trap small animals",
        "camera trap classification accuracy generalization", "camera trap class imbalance",
        "camera trap confidence calibration", "camera trap uncertainty classification",
        "camera trap false positive", "camera trap misclassification", "camera trap empty images",
        "camera trap image sequences classification", "camera trap human expert validation",
        "camera trap out of distribution", "camera trap open set recognition",
        "camera trap label noise", "camera trap evaluation deep learning",
    ],
}


def retrieve(topic, query):
    key = sha256(query.encode()).hexdigest()[:12]
    cache = ROOT / "raw" / (key + ".json")
    params = {"search": query,
              "filter": "type:article,primary_location.source.type:journal,is_retracted:false,to_publication_date:2026-10-24",
              "per-page": 60,
              "select": "id,doi,title,publication_year,publication_date,primary_location,type,authorships,cited_by_count,abstract_inverted_index,is_retracted,open_access"}
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    if cache.exists():
        return topic, query, json.loads(cache.read_text())
    errors = []
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Wildlitics-literature-discovery/1.0"})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = json.load(response)
            data["discovery"] = {"url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                                 "topic": topic, "query": query}
            cache.write_text(json.dumps(data, ensure_ascii=False))
            return topic, query, data
        except Exception as exc:
            errors.append(type(exc).__name__ + ": " + str(exc))
            time.sleep(1 + attempt)
    return topic, query, {"results": [], "error": errors, "url": url}


def main():
    (ROOT / "raw").mkdir(exist_ok=True)
    records, audit = {}, []
    tasks = [(topic, query) for topic, queries in QUERIES.items() for query in queries]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(retrieve, topic, query) for topic, query in tasks]
        for future in as_completed(futures):
            topic, query, data = future.result()
            audit.append({"topic": topic, "query": query, "returned": len(data["results"]),
                          "total_found": data.get("meta", {}).get("count"),
                          "error": data.get("error"), "request": data.get("discovery", {}).get("url", data.get("url"))})
            for item in data["results"]:
                key = (item.get("doi") or item["id"]).lower()
                if key not in records:
                    records[key] = {**item, "discovered_for": [], "matched_queries": []}
                if topic not in records[key]["discovered_for"]:
                    records[key]["discovered_for"].append(topic)
                if query not in records[key]["matched_queries"]:
                    records[key]["matched_queries"].append(query)
            print(f"{len(audit)}/{len(tasks)} searches; {len(records)} unique candidates", flush=True)
    (ROOT / "candidates.json").write_text(json.dumps(list(records.values()), ensure_ascii=False))
    (ROOT / "search-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
