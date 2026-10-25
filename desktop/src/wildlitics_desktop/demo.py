"""Explicit synthetic six-camera project for interface and workflow exploration."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from .project import Project


def create_demo(folder):
    folder = Path(folder).resolve()
    if (folder / "wildlitics.sqlite").exists():
        raise ValueError("Choose a new empty demo folder")
    project = Project(folder, create=True, name="Forest survey · synthetic demo")
    project.set_setting("synthetic_demo", "true")
    colours = ["#416e5b", "#88774e", "#477587", "#716153", "#6b794e", "#766481"]
    results = []
    for camera in range(1, 7):
        source = folder / "synthetic-images" / f"CAM-{camera:02}"
        source.mkdir(parents=True)
        ident = project.add_camera(f"CAM-{camera:02}", source)
        project.set_deployment(ident, "2026-10-01T00:00:00", "2026-10-08T00:00:00")
        for n in range(3):
            image = Image.new("RGB", (1000,650), "#182f2b")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0,440,1000,650), fill=colours[camera-1])
            draw.ellipse((340,230,620,490),fill="#b6bc8d")
            draw.text((40,40), f"SYNTHETIC FIXTURE / CAM-{camera:02} / {n+1}", fill="white")
            exif = Image.Exif();exif[306] = f"2026:10:0{n+1} {camera*3:02}:10:00"
            path = source / f"fixture-{n+1}.jpg"
            image.save(path, quality=90, exif=exif)
            label = "fixture;mammalia;carnivora;ursidae;helarctos;malayanus;sun bear" if camera%2 else "fixture-cat;mammalia;carnivora;felidae;neofelis;diardi;sunda clouded leopard"
            results.append({"filepath":str(path), "model_version":"SYNTHETIC-FIXTURE-NOT-INFERENCE",
                "detections":[{"category":"1","conf":.8,"bbox":[.34,.35,.28,.4],
                  "raw_classifications":{"classes":[label],"scores":[.72]},
                  "processed_classification":{"class":label,"score":.72,"source":"synthetic_fixture"}}]})
        project.scan_camera(ident)
    file = folder / "synthetic-predictions.json"
    file.write_text(json.dumps({"info":{"format_version":"20261015"},"predictions":results}),encoding="utf-8")
    result = project.import_predictions(file)
    for row in project.observations()[:10]:
        project.review(row["id"], "verified", row["taxon"], "Synthetic demo reviewer", "Interface fixture; not a real identification")
    project.close()
    return folder
