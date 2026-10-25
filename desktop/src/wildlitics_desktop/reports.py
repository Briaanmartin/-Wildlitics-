"""Descriptive reports from project records; no generated ecological conclusions."""
import csv
import base64
from datetime import datetime, timezone
import html
from io import BytesIO
import json
from pathlib import Path

from PIL import Image,ImageDraw


def activity_chart(hours):
    image=Image.new('RGB',(900,240),'#f5f8f1');draw=ImageDraw.Draw(image)
    maximum=max(hours) or 1
    for hour,count in enumerate(hours):
        x=45+hour*34;height=int(count/maximum*160)
        if count:draw.rounded_rectangle((x,190-height,x+23,190),radius=3,fill='#5d8860')
        if hour%3==0:draw.text((x,203),f'{hour:02}:00',fill='#425e48')
    draw.line((40,191,870,191),fill='#adc0a7')
    draw.text((42,17),'Observed encounter hours (camera-local EXIF time)',fill='#23432c')
    if not any(hours):draw.text((250,100),'No eligible timed records',fill='#6f7f6b')
    output=BytesIO();image.save(output,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(output.getvalue()).decode('ascii')


def report_html(project, *, camera_id=None, gap_minutes=30, verified_only=True):
    data = project.analysis(camera_id, gap_minutes=gap_minutes, verified_only=verified_only)
    esc = lambda x: html.escape(str(x))
    cameras = "".join("<tr>" + "".join("<td>" + esc(v) + "</td>" for v in [r["name"], r["images"],
        r["labelled_observations"], f"{r['declared_deployment_days']:.2f}" if r["declared_deployment_days"] is not None else "Not supplied",
        ", ".join(f"{k}: {v}" for k, v in r["processing_states"].items()) or "No imported images"]) + "</tr>" for r in data["cameras"])
    taxa = "".join(f"<tr><td>{esc(k)}</td><td>{v}</td><td>{data['encounters_with_time'].get(k,0)}</td></tr>" for k,v in data["taxon_labels"].items())
    bars = "".join(f'<tr><td>{hour:02}:00</td><td>{count}</td></tr>' for hour,count in enumerate(data["activity_hours"]))
    demo = '<p class="notice">SYNTHETIC DEMO — generated images and fixture predictions, not wildlife evidence.</p>' if data["synthetic_demo"] else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{esc(project.name)} — Wildlitics</title>
<style>body{{font:14px Arial,sans-serif;color:#183b35;max-width:1100px;margin:30px auto;padding:20px}}h1{{font-size:28px}}h2{{margin-top:28px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:9px;border:1px solid #c9d6cf;text-align:left}}th{{background:#edf3ed}}.notice{{padding:14px;background:#fff1d2}}pre{{white-space:pre-wrap;font-size:12px}}@media print{{body{{margin:0;padding:0}}}}</style></head><body>
<h1>{esc(project.name)}</h1><p>Wildlitics Desktop 0.1.0 · {datetime.now(timezone.utc).isoformat(timespec='seconds')}</p>{demo}
<p>Registered cameras: <b>{data['registered_cameras']}</b> · Selected cameras: <b>{data['selected_cameras']}</b> · Images: <b>{data['images']}</b></p>
<p>Observation policy: {'human-verified only' if verified_only else 'includes unverified AI suggestions'} · Encounter gap: {gap_minutes} minutes.</p>
<h2>Cameras and processing coverage</h2><table><tr><th>Camera</th><th>Images</th><th>Labelled observations</th><th>Declared deployment days</th><th>Processing</th></tr>{cameras}</table>
<h2>Taxon/category records</h2><p>Names are recorded labels and are not automatically validated species identities.</p><table><tr><th>Label</th><th>Observations</th><th>Encounters with capture time</th></tr>{taxa}</table>
<h2>Descriptive encounter hours</h2><p>Original camera-local EXIF times; missing or incorrect camera clocks require separate review.</p><img src="{activity_chart(data['activity_hours'])}" width="780" alt="Observed encounter-hour histogram"><table><tr><th>Hour</th><th>Encounters</th></tr>{bars}</table>
<h2>Method and limitations</h2><p>{esc(data['method'])}</p><p>Observations missing capture time: {data['observations_missing_capture_time']}. Missing times are excluded from encounter/hour counts. No animal detections is a processing result, not evidence of ecological absence. Scores are model outputs, not measured accuracy.</p>
<h2>Filters and processing states</h2><pre>{esc(json.dumps({'filters':data['filters'],'processing_states':data['processing_states'],'review_states':data['review_states']},indent=2))}</pre>
<h2>Model runs</h2><pre>{esc(json.dumps([{'id':r['id'],'status':r['status'],'created_utc':r['created_utc'],'parameters':{key:value for key,value in json.loads(r['parameters']).items() if key in {'country','threshold','model','source_sha256','expected_speciesnet_package'}}}for r in project.runs()],indent=2))}</pre>
<p>Original predictions, manifests and logs remain in the project runs folder. Review history remains in the project database.</p></body></html>"""


def write_report(project, output, **filters):
    path = Path(output)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(report_html(project, **filters))


def export_observations(project, output, camera_id=None, *, verified_only=False):
    fields = ["camera_name", "path", "captured", "scope", "bbox", "taxon", "common_name", "rank", "detector_score", "model_score", "decision_source", "review_state", "confirmed_taxon", "reviewer", "reviewed_utc", "note", "run_id"]
    with Path(output).open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in project.observations(camera_id):
            if verified_only and row['review_state'] != 'verified':
                continue
            writer.writerow({k:("'"+str(row[k]) if isinstance(row.get(k),str) and row[k].lstrip().startswith(("=","+","-","@")) else row.get(k))for k in fields})
