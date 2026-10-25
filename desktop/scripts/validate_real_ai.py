"""Optional real GUI-to-model smoke check on a caller-supplied local image.

The same photo is repeated across three synthetic camera folders to check path
associations. This is a software integration test, never an accuracy benchmark.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import time

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')


def main():
    from PySide6.QtWidgets import QApplication
    from wildlitics_desktop.app import MainWindow,STYLE
    from wildlitics_desktop.project import Project,file_hash
    from wildlitics_desktop.reports import write_report,export_observations
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--ai-python',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='New validation project directory')
    args=parser.parse_args();folder=args.output.resolve()
    if folder.exists():raise SystemExit('Choose a new output directory')
    original=file_hash(args.image);project=Project(folder,create=True,name='Real AI integration smoke')
    for n in range(1,4):
        source=folder/'validation-images'/f'CAM-{n:02}';source.mkdir(parents=True)
        shutil.copyfile(args.image,source/args.image.name)
        ident=project.add_camera(f'CAM-{n:02}',source);project.scan_camera(ident)
    project.close()
    app=QApplication([]);app.setStyleSheet(STYLE);window=MainWindow(folder);window.show();app.processEvents()
    failures=[];window.error=lambda message:failures.append(str(message))
    window.ai_python.setText(str(args.ai_python));window.start_ai()
    if window.worker is None:raise RuntimeError('AI worker did not start: '+';'.join(failures))
    started=time.monotonic();deadline=started+240
    while window.worker is not None:
        app.processEvents();time.sleep(.03)
        if time.monotonic()>deadline:
            window.cancel_job();raise RuntimeError('Real AI smoke timed out; check the project log')
    if failures:raise RuntimeError(';'.join(failures))
    project=window.project;run=project.runs()[0];rows=project.observations()
    assert run['status']=='complete',run
    assert len(project.cameras())==3 and len(project.images())==3
    assert len(rows)>=3 and {r['camera_name']for r in rows}=={'CAM-01','CAM-02','CAM-03'}
    assert all(r['review_state']=='unreviewed'for r in rows)
    assert window.coverage.rowCount()==3
    row=rows[0];project.review(row['id'],'verified',row['taxon']or row['common_name']or'Unresolved','Integration smoke reviewer','Workflow check, not independent species validation')
    window.refresh();assert window.coverage.rowCount()==3
    write_report(project,folder/'reviewed-report.html');export_observations(project,folder/'reviewed-observations.csv',verified_only=True)
    window.navigate(3);window.review_table.selectRow(0);app.processEvents();window.grab().save(str(folder/'real-ai-review.png'))
    assert file_hash(args.image)==original
    record={'passed':True,'platform':platform.platform(),'elapsed_inference_and_probe_seconds':round(time.monotonic()-started,2),
            'registered_synthetic_camera_folders':3,'distinct_source_photos':1,'source_photo_sha256':original,
            'images_processed':3,'observations':len(rows),'all_predictions_initially_unverified':True,
            'verified_by_explicit_review_action':1,'camera_count_preserved_after_review_filter':3,
            'original_unchanged':True,'predicted_taxa':sorted({r['taxon']or r['common_name']or'Unresolved'for r in rows}),
            'model':'kaggle:google/speciesnet/pyTorch/v4.0.3a/1','speciesnet_package':'5.0.6','default_detector':'MegaDetector v5a',
            'field_accuracy_measured':False,'source_photo_redistributed_with_application':False,
            'limitation':'A single caller-provided photo repeated across three synthetic camera folders; inference success does not measure wildlife accuracy.'}
    (folder/'real-ai-validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2));window.close()


if __name__=='__main__':main()
