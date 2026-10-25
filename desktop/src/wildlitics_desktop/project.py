"""Project persistence, camera intake and auditable per-object review."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import uuid

from PIL import Image, ImageOps

from .speciesnet_results import normalise_results

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cameras(
 id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,folder TEXT NOT NULL UNIQUE,
 started TEXT,ended TEXT,added_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS media(
 id INTEGER PRIMARY KEY,camera_id INTEGER NOT NULL REFERENCES cameras(id),
 path TEXT NOT NULL UNIQUE,source_sha256 TEXT NOT NULL,captured TEXT,
 width INTEGER,height INTEGER,import_error TEXT,
 processing_state TEXT NOT NULL DEFAULT 'pending',last_run_id TEXT);
CREATE TABLE IF NOT EXISTS runs(
 id TEXT PRIMARY KEY,kind TEXT NOT NULL,status TEXT NOT NULL,created_utc TEXT NOT NULL,
 finished_utc TEXT,parameters TEXT NOT NULL,folder TEXT NOT NULL,error TEXT);
CREATE TABLE IF NOT EXISTS predictions(
 run_id TEXT NOT NULL REFERENCES runs(id),media_id INTEGER NOT NULL REFERENCES media(id),
 raw_json TEXT NOT NULL,PRIMARY KEY(run_id,media_id));
CREATE TABLE IF NOT EXISTS observations(
 id INTEGER PRIMARY KEY,media_id INTEGER NOT NULL REFERENCES media(id),
 run_id TEXT NOT NULL REFERENCES runs(id),object_key TEXT NOT NULL,scope TEXT NOT NULL,
 bbox TEXT,detector_score REAL,model_score REAL,raw_label TEXT,taxon TEXT,rank TEXT,
 common_name TEXT,decision_source TEXT,candidates TEXT NOT NULL,
 review_state TEXT NOT NULL DEFAULT 'unreviewed',confirmed_taxon TEXT,reviewer TEXT,
 reviewed_utc TEXT,note TEXT,UNIQUE(run_id,media_id,object_key));
CREATE TABLE IF NOT EXISTS review_history(
 id INTEGER PRIMARY KEY,observation_id INTEGER NOT NULL REFERENCES observations(id),
 changed_utc TEXT NOT NULL,before_json TEXT NOT NULL,after_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS observations_media ON observations(media_id);
CREATE INDEX IF NOT EXISTS media_camera ON media(camera_id);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_hash(path):
    result = sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def path_key(path):
    return os.path.normcase(str(Path(path).expanduser().resolve()))


class Project:
    def __init__(self, folder, *, create=False, name=None):
        self.folder = Path(folder).resolve()
        database = self.folder / "wildlitics.sqlite"
        if not create and not database.is_file():
            raise ValueError("Choose a project folder containing wildlitics.sqlite")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(database, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        version = self.setting("schema_version")
        if version not in {None, "1"}:
            self.db.close()
            raise ValueError("Unsupported project database version")
        self.set_setting("schema_version", "1")
        if self.setting("name") is None:
            self.set_setting("name", name or self.folder.name)
        (self.folder / "runs").mkdir(exist_ok=True)

    def close(self):
        self.db.close()

    def setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))

    @property
    def name(self):
        return self.setting("name", self.folder.name)

    def cameras(self):
        return [dict(r) for r in self.db.execute("""
            SELECT c.*,COUNT(m.id) AS images,
              SUM(CASE WHEN m.processing_state='pending' THEN 1 ELSE 0 END) AS pending,
              SUM(CASE WHEN m.processing_state='failed' THEN 1 ELSE 0 END) AS failed
            FROM cameras c LEFT JOIN media m ON m.camera_id=c.id
            GROUP BY c.id ORDER BY c.name COLLATE NOCASE,c.id""")]

    def add_camera(self, name, folder):
        name = name.strip()
        source = Path(folder).resolve()
        if not name or not source.is_dir():
            raise ValueError("A unique camera name and existing image folder are required")
        key = path_key(source)
        for existing in self.cameras():
            if existing["name"].casefold() == name.casefold():
                raise ValueError("That camera ID already exists; use a distinct camera ID")
            other = Path(existing["folder"])
            if source == other or source in other.parents or other in source.parents:
                raise ValueError("Camera folders cannot overlap; select one folder per camera")
        with self.db:
            cursor = self.db.execute("INSERT INTO cameras(name,folder,added_utc)VALUES(?,?,?)", (name, key, now()))
        return cursor.lastrowid

    def set_deployment(self, camera_id, started, ended):
        values = []
        for value in (started, ended):
            values.append(datetime.fromisoformat(value).isoformat() if value else None)
        if bool(values[0]) != bool(values[1]):
            raise ValueError("Provide both deployment dates, or leave both empty")
        if values[0]:
            a, b = map(datetime.fromisoformat, values)
            if (a.tzinfo is None) != (b.tzinfo is None) or b <= a:
                raise ValueError("End must follow start, with matching timezone conventions")
        with self.db:
            self.db.execute("UPDATE cameras SET started=?,ended=? WHERE id=?", (*values, camera_id))

    def scan_camera(self, camera_id, progress=None, cancelled=None):
        camera = self.db.execute("SELECT * FROM cameras WHERE id=?", (camera_id,)).fetchone()
        if not camera:
            raise ValueError("Camera not found")
        source = Path(camera["folder"])
        if not source.is_dir():
            raise ValueError("The camera folder is unavailable")
        paths = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
        added, skipped, errors = 0, 0, 0
        for n, path in enumerate(paths, 1):
            if cancelled and cancelled():
                break
            key = path_key(path)
            if self.db.execute("SELECT id FROM media WHERE path=?", (key,)).fetchone():
                skipped += 1
                continue
            captured, width, height, error = None, None, None, None
            try:
                digest = file_hash(path)
                with Image.open(path) as img:
                    exif = img.getexif()
                    extra = exif.get_ifd(34665) if 34665 in exif else {}
                    raw = extra.get(36867) or exif.get(36867) or exif.get(306)
                    if raw:
                        try:
                            captured = datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S").isoformat()
                        except ValueError:
                            pass
                    oriented = ImageOps.exif_transpose(img)
                    width, height = oriented.size
                    oriented.load()
            except (OSError, ValueError, Image.DecompressionBombError) as exc:
                error = type(exc).__name__ + ": " + str(exc)
                digest = file_hash(path) if path.is_file() else "unavailable"
                errors += 1
            with self.db:
                self.db.execute("""INSERT INTO media(camera_id,path,source_sha256,captured,width,height,import_error,processing_state)
                    VALUES(?,?,?,?,?,?,?,?)""", (camera_id, key, digest, captured, width, height, error, "failed" if error else "pending"))
            added += 1
            if progress:
                progress(n, len(paths), path.name)
        return {"added": added, "already_imported": skipped, "unreadable": errors}

    def images(self, camera_id=None):
        sql = "SELECT m.*,c.name AS camera_name FROM media m JOIN cameras c ON c.id=m.camera_id"
        args = ()
        if camera_id is not None:
            sql += " WHERE c.id=?"
            args = (camera_id,)
        return [dict(r) for r in self.db.execute(sql + " ORDER BY c.name,m.path", args)]

    def create_run(self, parameters, *, kind="speciesnet"):
        ident = uuid.uuid4().hex
        folder = self.folder / "runs" / ident
        folder.mkdir()
        with self.db:
            self.db.execute("INSERT INTO runs(id,kind,status,created_utc,parameters,folder)VALUES(?,?,?,?,?,?)",
                            (ident, kind, "created", now(), json.dumps(parameters, allow_nan=False), str(folder)))
        return self.run(ident)

    def run(self, ident):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (ident,)).fetchone()
        if not row:
            raise ValueError("Run not found")
        return dict(row)

    def runs(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM runs ORDER BY created_utc DESC,rowid DESC")]

    def finish_run(self, ident, status, error=None):
        with self.db:
            self.db.execute("UPDATE runs SET status=?,error=?,finished_utc=? WHERE id=?", (status, error, now(), ident))

    def prepare_run(self, camera_id=None, *, country="", threshold=.1, model="kaggle:google/speciesnet/pyTorch/v4.0.3a/1", all_images=False):
        import math
        import re
        if country and not re.fullmatch(r"[A-Z]{3}", country):
            raise ValueError("Use a three-letter country code such as IDN, or leave it blank")
        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("Detector threshold must be between 0 and 1")
        images = [r for r in self.images(camera_id) if not r["import_error"]
                  and (all_images or r["processing_state"] in {"pending", "failed"})]
        if not images:
            raise ValueError("No eligible images. Import a camera or select 'Reprocess all'.")
        # Reuse is tied to immutable image contents, not merely to a filename.
        for item in images:
            if not Path(item["path"]).is_file() or file_hash(item["path"]) != item["source_sha256"]:
                raise ValueError("An imported image has changed or is missing: " + item["path"])
        params = {"country": country, "threshold": threshold, "model": model,
                  "media": [{"id": r["id"], "path": r["path"], "sha256": r["source_sha256"]} for r in images]}
        run = self.create_run(params)
        instances = [{"filepath": r["path"], **({"country": country} if country else {})} for r in images]
        (Path(run["folder"]) / "instances.json").write_text(json.dumps({"instances": instances}, indent=2), encoding="utf-8")
        return run

    def import_predictions(self, source, *, run_id=None, base_folder=None):
        source = Path(source).resolve()
        content = source.read_bytes()
        def bad_constant(value):
            raise ValueError("Invalid non-finite JSON number: " + value)
        payload = json.loads(content, parse_constant=bad_constant)
        result = normalise_results(payload)
        known = {path_key(r["path"]): r for r in self.images()}
        matches, unmatched = [], []
        for image in result["images"]:
            path = Path(image["filepath"])
            key = path_key(path if path.is_absolute() else Path(base_folder or source.parent) / path)
            media = known.get(key)
            if media is None:
                unmatched.append(image["filepath"])
                continue
            if not Path(media["path"]).is_file() or file_hash(media["path"]) != media["source_sha256"]:
                raise ValueError("Source image changed since import: " + media["path"])
            matches.append((image, media))
        if not matches:
            raise ValueError("No result paths match this project's images. Relative paths use the selected image root.")
        if run_id is None:
            digest = sha256(content).hexdigest()
            previous = next((r for r in self.runs() if r['kind']=='import'
                             and json.loads(r['parameters']).get('source_sha256')==digest), None)
            run = previous or self.create_run({"source_sha256": digest, "source_path": str(source)}, kind="import")
            run_id = run["id"]
            if previous is None:
                (Path(run["folder"]) / "source-predictions.json").write_bytes(content)
        run = self.run(run_id)
        expected = {r["id"] for r in json.loads(run["parameters"]).get("media", [])}
        if expected and any(media["id"] not in expected for _, media in matches):
            raise ValueError("Predictions contain images outside the selected inference job")
        added, skipped = 0, 0
        with self.db:
            for image, media in matches:
                exists = self.db.execute("SELECT 1 FROM predictions WHERE run_id=? AND media_id=?", (run_id, media["id"])).fetchone()
                if exists:
                    skipped += 1
                    continue
                self.db.execute("INSERT INTO predictions VALUES(?,?,?)", (run_id, media["id"], json.dumps(image["raw_prediction"])))
                for det in image["detections"]:
                    self._insert_observation(media["id"], run_id, str(det["detection_index"]), det["classification_scope"],
                        det["bbox_normalised_xywh"], det["detector_score"], det["raw_candidates"], det["suggestion"])
                legacy = image.get("image_classification")
                if legacy:
                    self._insert_observation(media["id"], run_id, "image", "image_unassociated", None, None,
                                             legacy["raw_candidates"], legacy["suggestion"])
                state = "failed" if image["failures"] else "no_detections" if not image["detections"] and not legacy else "complete"
                self.db.execute("UPDATE media SET processing_state=?,last_run_id=? WHERE id=?", (state, run_id, media["id"]))
                added += 1
        if run['kind']=='import':
            self.finish_run(run_id,'complete' if not unmatched else 'complete_with_unmatched')
        return {"images_imported": added, "already_imported": skipped, "unmatched_paths": unmatched}

    def _insert_observation(self, media_id, run_id, key, scope, box, detector_score, raw, suggestion):
        info = (suggestion or {}).get("taxon", {})
        self.db.execute("""INSERT INTO observations(media_id,run_id,object_key,scope,bbox,detector_score,model_score,
            raw_label,taxon,rank,common_name,decision_source,candidates)VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (media_id, run_id, key, scope, json.dumps(box) if box else None, detector_score,
             (suggestion or {}).get("ensemble_score"), info.get("raw_label"), info.get("scientific_name"),
             info.get("rank"), info.get("common_name"), (suggestion or {}).get("decision_source"), json.dumps(raw)))

    def observations(self, camera_id=None, review_state=None):
        sql = """SELECT o.*,m.path,m.captured,m.camera_id,c.name AS camera_name,m.processing_state
            FROM observations o JOIN media m ON m.id=o.media_id JOIN cameras c ON c.id=m.camera_id
            WHERE o.run_id=m.last_run_id"""
        args = []
        if camera_id is not None:
            sql += " AND c.id=?"
            args.append(camera_id)
        if review_state:
            sql += " AND o.review_state=?"
            args.append(review_state)
        return [dict(r) for r in self.db.execute(sql + " ORDER BY c.name,m.path,o.id", args)]

    def review(self, ident, state, label, reviewer, note=""):
        if state not in {"verified", "rejected", "unreviewed"}:
            raise ValueError("Unknown review state")
        if state != "unreviewed" and not reviewer.strip():
            raise ValueError("A reviewer name is required")
        if state == "verified" and not label.strip():
            raise ValueError("Enter the human-confirmed taxon/category")
        old = self.db.execute("SELECT * FROM observations WHERE id=?", (ident,)).fetchone()
        if old is None:
            raise ValueError("Observation not found")
        changes = {"review_state": state, "confirmed_taxon": label.strip() if state == "verified" else None,
                   "reviewer": reviewer.strip(), "reviewed_utc": now(), "note": note.strip()}
        with self.db:
            self.db.execute("""UPDATE observations SET review_state=:review_state,confirmed_taxon=:confirmed_taxon,
                reviewer=:reviewer,reviewed_utc=:reviewed_utc,note=:note WHERE id=:id""", {**changes, "id": ident})
            self.db.execute("INSERT INTO review_history(observation_id,changed_utc,before_json,after_json)VALUES(?,?,?,?)",
                            (ident, now(), json.dumps(dict(old)), json.dumps(changes)))

    def analysis(self, camera_id=None, *, gap_minutes=30, verified_only=True):
        if gap_minutes not in {0, 30, 60}:
            raise ValueError("Choose no grouping, 30 minutes or 60 minutes")
        cameras = [c for c in self.cameras() if camera_id is None or c["id"] == camera_id]
        images = self.images(camera_id)
        observations = self.observations(camera_id)
        rows = [r for r in observations if r["review_state"] == "verified"] if verified_only else [r for r in observations if r["review_state"] != "rejected"]
        taxa, by_camera, timeline = Counter(), Counter(), defaultdict(list)
        missing_times = 0
        for r in rows:
            label = r["confirmed_taxon"] if r["review_state"] == "verified" else r["taxon"]
            if not label:
                continue
            taxa[label] += 1
            by_camera[r["camera_id"]] += 1
            if r["captured"]:
                timeline[(r["camera_id"], label)].append((datetime.fromisoformat(r["captured"]), r["media_id"]))
            else:
                missing_times += 1
        events, hours = Counter(), [0] * 24
        for (_, label), records in timeline.items():
            previous = None
            # Multiple same-species boxes in one image share one encounter timestamp.
            for stamp, _ in sorted(set(records)):
                if previous is None or (stamp - previous).total_seconds() >= gap_minutes * 60:
                    events[label] += 1
                    hours[stamp.hour] += 1
                previous = stamp
        camera_rows = []
        for camera in cameras:
            subset = [r for r in images if r["camera_id"] == camera["id"]]
            duration = None
            if camera["started"] and camera["ended"]:
                duration = (datetime.fromisoformat(camera["ended"]) - datetime.fromisoformat(camera["started"])).total_seconds() / 86400
            camera_rows.append({"id": camera["id"], "name": camera["name"], "images": len(subset),
                                "labelled_observations": by_camera[camera["id"]], "declared_deployment_days": duration,
                                "processing_states": dict(Counter(r["processing_state"] for r in subset))})
        return {"project": self.name, "synthetic_demo": self.setting("synthetic_demo", "false") == "true",
                "filters": {"camera_id": camera_id, "verified_only": verified_only, "encounter_gap_minutes": gap_minutes},
                "registered_cameras": len(self.cameras()), "selected_cameras": len(cameras), "images": len(images),
                "processing_states": dict(Counter(r["processing_state"] for r in images)),
                "review_states": dict(Counter(r["review_state"] for r in observations)),
                "taxon_labels": dict(taxa.most_common()), "encounters_with_time": dict(events), "activity_hours": hours,
                "observations_missing_capture_time": missing_times, "cameras": camera_rows,
                "method": "Same camera/taxon records are grouped using a gap from the previous detection. Activity is a descriptive encounter-hour histogram, not an estimate of time active. Declared deployment durations assume continuous operation and are not validated trap-days. Counts are observations/encounters, not individual animals or population estimates."}
