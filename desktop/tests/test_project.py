"""Workflow checks using generated images and explicit synthetic predictions."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from PIL import Image

from wildlitics_desktop.ai import command_for_run, run_process
from wildlitics_desktop.project import Project
from wildlitics_desktop.reports import export_observations, report_html, write_report

BEAR="fixture;mammalia;carnivora;ursidae;helarctos;malayanus;sun bear"
CAT="fixture-cat;mammalia;carnivora;felidae;neofelis;diardi;sunda clouded leopard"


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.project=Project(self.root/'project',create=True,name='Test <survey>')

    def tearDown(self):
        self.project.close();self.tmp.cleanup()

    def camera(self,name='CAM-01',images=1):
        folder=self.root/name;folder.mkdir()
        for n in range(images):
            image=Image.new('RGB',(60,40),(n*20,80,100));exif=Image.Exif();exif[306]=f'2026:10:01 0{n}:00:00'
            image.save(folder/f'{n}.jpg',exif=exif)
        ident=self.project.add_camera(name,folder);self.project.scan_camera(ident)
        return ident

    def predictions(self,images=None, *, failure=False, legacy=False):
        rows=[]
        for image in images or self.project.images():
            det={'category':'1','conf':.85,'bbox':[.1,.2,.3,.4]}
            value={'filepath':image['path'],'model_version':'TEST-FIXTURE','detections':[det]}
            if failure:value['failures']=['CLASSIFIER']
            elif legacy:value.update(classifications={'classes':[BEAR],'scores':[.7]},prediction=BEAR,prediction_score=.7,prediction_source='classifier')
            else:det.update(raw_classifications={'classes':[BEAR],'scores':[.7]},processed_classification={'class':BEAR,'score':.7,'source':'classifier'})
            rows.append(value)
        path=self.root/'predictions.json'
        path.write_text(json.dumps({'predictions':rows,**({}if legacy else {'info':{'format_version':'20261015'}})}))
        return path

    def test_all_registered_cameras_remain_visible_with_zero_verified_records(self):
        for n in range(9):self.camera(f'CAM-{n:02}',images=0 if n==8 else 1)
        result=self.project.analysis()
        self.assertEqual((result['registered_cameras'],result['selected_cameras']), (9,9))
        self.assertEqual(len(result['cameras']),9)
        self.assertEqual(result['taxon_labels'],{})
        self.assertEqual(result['cameras'][-1]['images'],0)

    def test_duplicate_and_overlapping_camera_roots_are_rejected(self):
        ident=self.camera()
        with self.assertRaisesRegex(ValueError,'already exists'):self.project.add_camera('cam-01',self.root)
        with self.assertRaisesRegex(ValueError,'overlap'):self.project.add_camera('another',self.root)

    def test_rescanning_preserves_original_and_does_not_duplicate_media(self):
        ident=self.camera();image=self.project.images()[0];before=Path(image['path']).read_bytes()
        result=self.project.scan_camera(ident)
        self.assertEqual(result['already_imported'],1)
        self.assertEqual(len(self.project.images()),1)
        self.assertEqual(Path(image['path']).read_bytes(),before)

    def test_missing_exif_stays_unknown_and_unreadable_is_failed(self):
        folder=self.root/'camera';folder.mkdir();Image.new('RGB',(20,20)).save(folder/'none.png');(folder/'bad.jpg').write_bytes(b'bad image')
        ident=self.project.add_camera('A',folder);self.project.scan_camera(ident)
        rows=self.project.images()
        self.assertTrue(all(x['captured']is None for x in rows))
        self.assertEqual({x['processing_state']for x in rows},{'pending','failed'})

    def test_prediction_import_and_human_review_history(self):
        self.camera();self.project.import_predictions(self.predictions());row=self.project.observations()[0]
        self.assertEqual(row['scope'],'detection');self.assertEqual(row['taxon'],'helarctos malayanus')
        self.assertEqual(self.project.analysis()['taxon_labels'],{})
        self.project.review(row['id'],'verified','Helarctos malayanus','Expert','Reviewed fixture')
        self.assertEqual(self.project.analysis()['taxon_labels'],{'Helarctos malayanus':1})
        self.project.review(row['id'],'rejected','','Expert','Correction')
        self.assertEqual(self.project.db.execute('SELECT COUNT(*)FROM review_history').fetchone()[0],2)
        self.assertEqual(self.project.analysis()['taxon_labels'],{})

    def test_reviews_require_a_reviewer_and_verified_label(self):
        self.camera();self.project.import_predictions(self.predictions());ident=self.project.observations()[0]['id']
        for label,reviewer in [('Helarctos malayanus',''),('','Expert')]:
            with self.assertRaises(ValueError):self.project.review(ident,'verified',label,reviewer)

    def test_legacy_image_labels_are_not_attributed_to_animal_boxes(self):
        self.camera();self.project.import_predictions(self.predictions(legacy=True));rows=self.project.observations()
        self.assertEqual(len(rows),2)
        box=next(r for r in rows if r['scope']=='detection');whole=next(r for r in rows if r['scope']=='image_unassociated')
        self.assertIsNone(box['taxon']);self.assertEqual(whole['taxon'],'helarctos malayanus');self.assertIsNone(whole['bbox'])

    def test_import_is_idempotent_within_a_saved_run(self):
        self.camera();run=self.project.prepare_run();source=self.predictions()
        self.project.import_predictions(source,run_id=run['id'])
        result=self.project.import_predictions(source,run_id=run['id'])
        self.assertEqual(result['already_imported'],1);self.assertEqual(len(self.project.observations()),1)

    def test_reimporting_same_json_preserves_review_and_latest_run(self):
        self.camera();source=self.predictions();self.project.import_predictions(source)
        row=self.project.observations()[0];self.project.review(row['id'],'verified','Helarctos malayanus','Expert')
        result=self.project.import_predictions(source)
        self.assertEqual(result['already_imported'],1)
        self.assertEqual(self.project.observations()[0]['review_state'],'verified')
        self.assertEqual(len(self.project.runs()),1)

    def test_verified_csv_filter_matches_reporting_policy(self):
        import csv
        self.camera(images=2);self.project.import_predictions(self.predictions());row=self.project.observations()[0]
        self.project.review(row['id'],'verified','Helarctos malayanus','Expert')
        output=self.root/'verified.csv';export_observations(self.project,output,verified_only=True)
        with output.open(encoding='utf-8-sig')as handle:rows=list(csv.DictReader(handle))
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['review_state'],'verified')

    def test_partial_failure_is_preserved_not_counted_as_empty(self):
        self.camera();self.project.import_predictions(self.predictions(failure=True))
        self.assertEqual(self.project.images()[0]['processing_state'],'failed')
        self.assertEqual(len(self.project.observations()),1)

    def test_changed_source_blocks_run_and_result_import(self):
        self.camera();source=self.predictions();Path(self.project.images()[0]['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):self.project.prepare_run()
        with self.assertRaisesRegex(ValueError,'changed'):self.project.import_predictions(source)
        self.assertEqual(self.project.observations(),[])

    def test_unmatched_path_is_not_guessed_from_filename(self):
        self.camera();path=self.predictions();payload=json.loads(path.read_text());payload['predictions'][0]['filepath']='somewhere-else/0.jpg';path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError,'No result paths match'):self.project.import_predictions(path)

    def test_dataset_and_camera_filters_are_separate(self):
        a=self.camera('A');b=self.camera('B');self.project.import_predictions(self.predictions())
        one=self.project.analysis(a,verified_only=False)
        self.assertEqual(one['registered_cameras'],2);self.assertEqual(one['selected_cameras'],1)
        self.assertEqual(one['taxon_labels'],{'helarctos malayanus':1})

    def test_deployment_duration_requires_explicit_metadata(self):
        ident=self.camera();self.assertIsNone(self.project.analysis()['cameras'][0]['declared_deployment_days'])
        self.project.set_deployment(ident,'2026-10-01T00:00:00','2026-10-08T00:00:00')
        self.assertEqual(self.project.analysis()['cameras'][0]['declared_deployment_days'],7)
        with self.assertRaises(ValueError):self.project.set_deployment(ident,'2026-10-09','2026-10-01')

    def test_job_command_uses_argument_list_and_saved_inputs(self):
        self.camera();run=self.project.prepare_run(country='IDN');command=command_for_run(sys.executable,run)
        self.assertEqual(command[0],sys.executable)
        self.assertIn('speciesnet.scripts.run_model',command)
        self.assertIn(str(Path(run['folder'])/'instances.json'),command)
        self.assertEqual(json.loads((Path(run['folder'])/'instances.json').read_text())['instances'][0]['country'],'IDN')

    def test_reports_preserve_sources_escape_labels_and_refuse_overwrite(self):
        self.camera();self.project.import_predictions(self.predictions())
        html=report_html(self.project,verified_only=False)
        self.assertIn('Test &lt;survey&gt;',html);self.assertIn('assume continuous operation',html)
        output=self.root/'report.html';write_report(self.project,output)
        with self.assertRaises(FileExistsError):write_report(self.project,output)
        row=self.project.observations()[0];self.project.review(row['id'],'verified','=formula','Reviewer')
        export=self.root/'observations.csv';export_observations(self.project,export)
        self.assertIn("'=formula",export.read_text(encoding='utf-8-sig'))


class ProcessTests(unittest.TestCase):
    def test_silent_process_can_be_cancelled_without_waiting_for_output(self):
        with tempfile.TemporaryDirectory() as folder:
            event=threading.Event();timer=threading.Timer(.4,event.set);timer.start();started=time.monotonic()
            result=run_process([sys.executable,'-c','import time;time.sleep(60)'],Path(folder)/'log.txt',cancelled=event)
            timer.join()
            self.assertTrue(result['cancelled']);self.assertLess(time.monotonic()-started,12)

    def test_failure_logs_and_exit_code_are_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'log.txt'
            result=run_process([sys.executable,'-c',"print('failure fixture');raise SystemExit(3)"],path)
            self.assertEqual(result['returncode'],3);self.assertIn('failure fixture',path.read_text())


if __name__=='__main__':unittest.main()
