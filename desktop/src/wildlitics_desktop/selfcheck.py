"""A packaged-app smoke check writes its result to a user-selected file."""
import json
import os
from pathlib import Path
import sys
import tempfile


def main():
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPdfWriter,QTextDocument
    from .app import MainWindow,STYLE
    from .demo import create_demo
    from .reports import report_html
    output=Path(sys.argv[sys.argv.index('--self-test')+1]).resolve()
    try:
        app=QApplication.instance()or QApplication([]);app.setStyleSheet(STYLE)
        with tempfile.TemporaryDirectory()as temp:
            folder=create_demo(Path(temp)/'demo');window=MainWindow(folder);window.show();app.processEvents()
            assert window.camera_filter.count()-1==6
            assert window.coverage.rowCount()==6 and window.metrics[0].text()=='6'
            window.verified.setChecked(False);app.processEvents();assert window.coverage.rowCount()==6
            window.navigate(3);window.review_table.selectRow(0);app.processEvents();assert not window.photo.image.isNull()
            writer=QPdfWriter(str(Path(temp)/'report.pdf'));document=QTextDocument();document.setHtml(report_html(window.project));document.print_(writer)
            assert (Path(temp)/'report.pdf').read_bytes().startswith(b'%PDF')
            window.close()
        output.write_text(json.dumps({'passed':True,'registered_cameras':6,'filter_keeps_all_cameras':True,'review_image_loaded':True,'pdf_export':True,'inference_performed':False},indent=2)+'\n')
        return 0
    except Exception as exc:
        output.write_text(json.dumps({'passed':False,'error':type(exc).__name__+': '+str(exc)},indent=2)+'\n')
        return 1
