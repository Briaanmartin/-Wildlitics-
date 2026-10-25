"""Offscreen native UI checks; no cloud or wildlife model execution."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import tempfile
import unittest

from PySide6.QtGui import QPdfWriter,QTextDocument
from PySide6.QtWidgets import QApplication

from wildlitics_desktop.app import MainWindow,STYLE
from wildlitics_desktop.demo import create_demo
from wildlitics_desktop.reports import report_html


class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance()or QApplication([]);cls.app.setStyleSheet(STYLE)

    def test_six_camera_demo_survives_review_filters_and_reopens(self):
        with tempfile.TemporaryDirectory() as root:
            folder=create_demo(Path(root)/'demo');window=MainWindow(folder);window.show();self.app.processEvents()
            self.assertEqual(window.camera_filter.count()-1,6)
            self.assertEqual(window.metrics[0].text(),'6');self.assertEqual(window.coverage.rowCount(),6)
            window.verified.setChecked(False);self.app.processEvents();self.assertEqual(window.coverage.rowCount(),6)
            window.camera_filter.setCurrentIndex(6);self.app.processEvents()
            self.assertEqual(window.coverage.rowCount(),1);self.assertEqual(window.metrics[0].text(),'6')
            window.navigate(3);window.review_table.selectRow(0);self.app.processEvents()
            self.assertFalse(window.photo.image.isNull());self.assertIn('Scope:',window.observation_details.text())
            pdf=Path(root)/'report.pdf';writer=QPdfWriter(str(pdf));document=QTextDocument();document.setHtml(report_html(window.project));document.print_(writer)
            self.assertTrue(pdf.read_bytes().startswith(b'%PDF'))
            window.close();reopened=MainWindow(folder);self.assertEqual(reopened.metrics[0].text(),'6');reopened.close()


if __name__=='__main__':unittest.main()
