"""Native Qt desktop interface for local camera-trap AI and human review."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import threading

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QImageReader, QPainter, QPen, QPdfWriter, QTextDocument
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget)

from . import __version__
from .ai import DEFAULT_MODEL, command_for_run, default_ai_python, run_process, runtime_command
from .demo import create_demo
from .project import Project, file_hash
from .reports import export_observations, report_html, write_report

STYLE = """
QWidget {font-family:'Segoe UI','DejaVu Sans';font-size:13px;color:#213b34;background:#f4f6f1;}
QMainWindow {background:#f4f6f1;} QLabel {background:transparent;}
QFrame#sidebar {background:#173c32;} QFrame#sidebar QLabel {color:#d5e5d6;}
QLabel#brand {font-size:26px;font-weight:700;color:white;} QLabel#eyebrow {color:#61776b;font-size:11px;font-weight:600;}
QLabel#title {font-size:26px;font-weight:700;} QLabel#subtitle {color:#687b70;}
QPushButton {background:white;border:1px solid #cfdbcf;border-radius:7px;padding:10px 15px;font-weight:600;}
QPushButton:hover {background:#e8eee2;border-color:#a2b29e;} QPushButton:disabled {color:#96a197;background:#edf0e8;}
QPushButton#primary {background:#275f45;color:white;border:1px solid #275f45;} QPushButton#primary:hover {background:#1d4c36;}
QPushButton#nav {background:transparent;color:#c7d7cb;border:0;text-align:left;padding:13px 16px;}
QPushButton#nav:checked {background:#305343;color:white;border-left:3px solid #c6d29b;border-radius:4px;}
QFrame#card {background:white;border:1px solid #dde4d8;border-radius:9px;} QLabel#metric {font-size:31px;font-weight:700;}
QLineEdit,QComboBox,QDoubleSpinBox {background:white;border:1px solid #cdd8ca;border-radius:6px;padding:8px;}
QComboBox::drop-down {border:0;width:24px;} QTableWidget {background:white;border:1px solid #dde4d8;gridline-color:#e9ede4;border-radius:6px;selection-background-color:#dfebd7;selection-color:#173c32;}
QHeaderView::section {background:#edf2e8;color:#556b5a;border:0;border-bottom:1px solid #dce5d5;padding:10px;text-align:left;font-weight:600;}
QTableWidget::item {padding:7px;} QPlainTextEdit,QTextBrowser {background:white;border:1px solid #dce5d5;border-radius:6px;padding:10px;}
QCheckBox {spacing:8px;} QSplitter::handle {background:#e3e9de;} QStatusBar {background:#e8ede2;}
"""


def label(text, name=None, wrap=False):
    item = QLabel(text)
    if name:
        item.setObjectName(name)
    item.setWordWrap(wrap)
    return item


def button(text, callback, primary=False):
    item = QPushButton(text)
    if primary:
        item.setObjectName("primary")
    item.clicked.connect(callback)
    return item


def card(title, value="—", detail=""):
    frame = QFrame();frame.setObjectName("card")
    box = QVBoxLayout(frame);box.setContentsMargins(18,14,18,14)
    box.addWidget(label(title.upper(), "eyebrow"))
    metric = label(value, "metric");box.addWidget(metric)
    box.addWidget(label(detail, "subtitle", True))
    return frame, metric


def table(headers):
    widget = QTableWidget(0,len(headers));widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    widget.verticalHeader().setVisible(False)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    widget.setAlternatingRowColors(False)
    return widget


def fill(widget, rows):
    widget.setRowCount(len(rows))
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            item=QTableWidgetItem(str(value if value is not None else "—"));item.setToolTip(item.text());widget.setItem(r,c,item)


class Work(QThread):
    done = Signal(object)
    failed = Signal(str)
    line = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent);self.fn=fn;self.cancelled=threading.Event()

    def run(self):
        try:
            self.done.emit(self.fn(self))
        except Exception as exc:
            self.failed.emit(type(exc).__name__+": "+str(exc))


class Bars(QWidget):
    def __init__(self, title, *, hourly=False):
        super().__init__();self.title=title;self.hourly=hourly;self.values=[]
        self.setMinimumHeight(230);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)

    def set_values(self, values):
        self.values=list(values);self.update()

    def paintEvent(self, event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#dce5d5"));painter.setBrush(QColor("white"));painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1),9,9)
        painter.setPen(QColor("#294435"));painter.setFont(QFont("Segoe UI",11,QFont.Weight.DemiBold));painter.drawText(20,30,self.title)
        if not self.values or max(v for _,v in self.values)==0:
            painter.setPen(QColor("#798b7c"));painter.setFont(QFont("Segoe UI",10));painter.drawText(20,80,"No eligible observations for these filters")
            return
        painter.setFont(QFont("Segoe UI",9));maximum=max(v for _,v in self.values)
        if self.hourly:
            bottom=self.height()-37;available=bottom-58;width=(self.width()-44)/24
            for n,(_,value) in enumerate(self.values):
                painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor("#69986a"));height=value/maximum*available
                painter.drawRoundedRect(int(23+n*width),int(bottom-height),max(2,int(width)-4),max(1,int(height)),3,3)
                if n%6==0:
                    painter.setPen(QColor("#6b7d6c"));painter.drawText(int(23+n*width),bottom+21,f"{n:02}:00")
            painter.setPen(QColor("#6b7d6c"));painter.drawText(23,54,f"Peak bin: {maximum} encounters")
        else:
            available=self.width()-225
            for n,(name,value) in enumerate(self.values[:6]):
                y=62+n*31;painter.setPen(QColor("#4f6653"));painter.drawText(20,y+12,name[:23])
                painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor("#dae6d1"));painter.drawRoundedRect(190,y,max(3,int(value/maximum*available)),17,3,3)
                painter.setPen(QColor("#294435"));painter.drawText(self.width()-31,y+13,str(value))


class Photo(QWidget):
    def __init__(self):
        super().__init__();self.image=None;self.box=None;self.setMinimumSize(280,230)

    def show_observation(self,row):
        self.image=None;self.box=None
        if row:
            reader=QImageReader(row["path"]);reader.setAutoTransform(True)
            self.image=reader.read();self.box=json.loads(row["bbox"]) if row["bbox"] else None
        self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor("#152d25"))
        if self.image is None or self.image.isNull():
            p.setPen(QColor("#c3d1c5"));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,"Select an observation to inspect its source image")
            return
        size=self.image.size();scale=min(self.width()/size.width(),self.height()/size.height())
        w,h=int(size.width()*scale),int(size.height()*scale);x,y=(self.width()-w)//2,(self.height()-h)//2
        p.drawImage(x,y,self.image.scaled(w,h,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        if self.box:
            bx,by,bw,bh=self.box;p.setPen(QPen(QColor("#d3e987"),2));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(int(x+bx*w),int(y+by*h),int(bw*w),int(bh*h))


class MainWindow(QMainWindow):
    def __init__(self, project=None):
        super().__init__();self.project=None;self.worker=None;self.current_run=None;self.rows=[]
        self.setWindowTitle("Wildlitics Desktop · Local wildlife AI");self.resize(1440,940)
        self.setMinimumSize(1060,680)
        central=QWidget();self.setCentralWidget(central);outer=QHBoxLayout(central);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        sidebar=QFrame();sidebar.setObjectName("sidebar");sidebar.setFixedWidth(215);nav=QVBoxLayout(sidebar);nav.setContentsMargins(18,27,18,22)
        nav.addWidget(label("Wildlitics", "brand"));nav.addWidget(label("FIELD DATA → INSIGHT"));nav.addSpacing(30)
        self.stack=QStackedWidget();self.nav_buttons=[]
        for n,title in enumerate(["Overview","Cameras","AI workbench","Review records","Reports"]):
            item=QPushButton(title);item.setObjectName("nav");item.setCheckable(True)
            item.clicked.connect(lambda checked=False,index=n:self.navigate(index));nav.addWidget(item);self.nav_buttons.append(item)
        nav.addStretch();nav.addWidget(label("DESKTOP PROTOTYPE 0.1.0"));nav.addWidget(label("Local files · Local inference",wrap=True))
        self.project_hint=label("No project open",wrap=True);nav.addWidget(self.project_hint)
        outer.addWidget(sidebar)
        content=QWidget();layout=QVBoxLayout(content);layout.setContentsMargins(26,22,26,18);layout.setSpacing(16)
        top=QHBoxLayout();heading=QVBoxLayout();heading.addWidget(label("WILDLITICS / LOCAL WORKSPACE", "eyebrow"));self.project_title=label("Open a wildlife project", "title");heading.addWidget(self.project_title)
        self.project_subtitle=label("Run wildlife AI, review each animal and keep survey records together.","subtitle");heading.addWidget(self.project_subtitle)
        top.addLayout(heading,1);top.addWidget(button("New project",self.new_project));top.addWidget(button("Open",self.open_project));top.addWidget(button("Try demo",self.demo_project))
        layout.addLayout(top)
        filters=QHBoxLayout();filters.addWidget(label("Camera"));self.camera_filter=QComboBox();self.camera_filter.setMinimumWidth(210);self.camera_filter.currentIndexChanged.connect(self.refresh_views);filters.addWidget(self.camera_filter)
        self.verified=QCheckBox("Verified records only");self.verified.setChecked(True);self.verified.toggled.connect(self.refresh_views);filters.addWidget(self.verified)
        filters.addWidget(label("Encounter gap"));self.gap=QComboBox();self.gap.addItem("30 minutes",30);self.gap.addItem("60 minutes",60);self.gap.addItem("No grouping",0);self.gap.currentIndexChanged.connect(self.refresh_views);filters.addWidget(self.gap);filters.addStretch();layout.addLayout(filters)
        self.make_overview();self.make_cameras();self.make_ai();self.make_review();self.make_reports()
        layout.addWidget(self.stack,1);outer.addWidget(content,1)
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage("Open or create a project. The demo uses synthetic fixtures, clearly marked throughout.")
        self.navigate(0)
        if project:
            self.load_project(project)

    def navigate(self,index):
        self.stack.setCurrentIndex(index)
        for n,item in enumerate(self.nav_buttons):item.setChecked(n==index)

    def make_overview(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        metrics=QHBoxLayout();self.metrics=[]
        for title,detail in [("Registered cameras","All cameras in this project"),("Selected images","Across the camera filter"),("Verified observations","Human-reviewed records"),("Awaiting review","Current model observations")]:
            frame,value=card(title,detail=detail);metrics.addWidget(frame);self.metrics.append(value)
        layout.addLayout(metrics)
        charts=QHBoxLayout();self.taxon_bars=Bars("Recorded taxon labels");self.hour_bars=Bars("Daily encounter times",hourly=True);charts.addWidget(self.taxon_bars);charts.addWidget(self.hour_bars);layout.addLayout(charts,1)
        layout.addWidget(label("CAMERA COVERAGE", "eyebrow"));self.coverage=table(["Camera","Images","Labelled records","Pending","Failed"]);layout.addWidget(self.coverage,1)
        self.quality=label("Add your camera folders to start. Every registered camera remains visible, including cameras with no eligible observations.","subtitle",True);layout.addWidget(self.quality)
        self.stack.addWidget(page)

    def make_cameras(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label("Camera folders", "title"));layout.addWidget(label("One folder and unique ID per camera. Register a collection of camera folders together; there is no two-camera display cap.","subtitle",True))
        actions=QHBoxLayout();actions.addWidget(button("Add camera folder",self.add_camera,True));actions.addWidget(button("Import camera collection",self.add_collection));actions.addWidget(button("Rescan folders",self.scan));actions.addWidget(button("Set deployment dates",self.deployment));actions.addStretch();layout.addLayout(actions)
        self.camera_table=table(["Camera ID","Source folder","Images","Pending","Failed","Deployment start","Deployment end"]);layout.addWidget(self.camera_table,1)
        layout.addWidget(label("Original photographs stay in their source folders. Missing EXIF times are kept as unknown; file modification dates are not substituted as capture dates.","subtitle",True));self.stack.addWidget(page)

    def make_ai(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label("Run wildlife AI", "title"));layout.addWidget(label("Official SpeciesNet 5.0.6 cascade: MegaDetector finds objects and SpeciesNet suggests taxa. Predictions remain unverified until you review them.","subtitle",True))
        grid=QGridLayout();grid.addWidget(label("AI environment Python"),0,0);self.ai_python=QLineEdit(default_ai_python());grid.addWidget(self.ai_python,0,1);grid.addWidget(button("Browse",self.browse_python),0,2);grid.addWidget(button("Check runtime",self.check_runtime),0,3)
        grid.addWidget(label("Model"),1,0);self.model=QComboBox();self.model.addItem("SpeciesNet 4.0.3a · animal crops",DEFAULT_MODEL);self.model.addItem("SpeciesNet 4.0.3b · whole image",DEFAULT_MODEL.replace("4.0.3a","4.0.3b"));grid.addWidget(self.model,1,1)
        self.country=QComboBox();self.country.addItem("No geographic filter","");self.country.addItem("Indonesia · IDN","IDN");self.country.addItem("Malaysia · MYS","MYS");self.country.addItem("United States · USA","USA");grid.addWidget(self.country,1,2,1,2)
        grid.addWidget(label("Detection threshold"),2,0);self.threshold=QDoubleSpinBox();self.threshold.setRange(0,1);self.threshold.setSingleStep(.05);self.threshold.setValue(.1);grid.addWidget(self.threshold,2,1)
        self.reprocess=QCheckBox("Reprocess all selected images");grid.addWidget(self.reprocess,2,2,1,2);layout.addLayout(grid)
        actions=QHBoxLayout();self.run_button=button("Run wildlife AI",self.start_ai,True);actions.addWidget(self.run_button);self.cancel_button=button("Cancel job",self.cancel_job);actions.addWidget(self.cancel_button);actions.addWidget(button("Import predictions JSON",self.import_predictions));actions.addWidget(button("AI setup guide",self.setup_guide));actions.addStretch();layout.addLayout(actions)
        history=QHBoxLayout();history.addWidget(label("Saved job"));self.run_history=QComboBox();history.addWidget(self.run_history,1);history.addWidget(button("Resume job",self.resume_ai));history.addWidget(button("Open project files",self.open_project_files));layout.addLayout(history)
        self.ai_state=label("Ready. First inference downloads the selected official model if it is not already cached.","subtitle",True);layout.addWidget(self.ai_state)
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(1800);self.log.setPlaceholderText("Runtime information, model downloads and inference progress appear here.");layout.addWidget(self.log,1)
        self.stack.addWidget(page)

    def make_review(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label("Inspect and verify", "title"));layout.addWidget(label("Review one object at a time. Model score is not measured accuracy. The review queue includes unverified records regardless of the dashboard's verification filter.","subtitle",True))
        splitter=QSplitter();self.review_table=table(["Camera","Suggested label","Score","Review"]);self.review_table.itemSelectionChanged.connect(self.select_observation);splitter.addWidget(self.review_table)
        for column in (0,2,3):self.review_table.horizontalHeader().setSectionResizeMode(column,QHeaderView.ResizeMode.ResizeToContents)
        self.review_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        panel=QWidget();right=QVBoxLayout(panel);right.setContentsMargins(12,0,0,0);self.photo=Photo();right.addWidget(self.photo,2)
        self.observation_details=label("Select a record.","subtitle",True);right.addWidget(self.observation_details)
        self.candidates=QPlainTextEdit();self.candidates.setReadOnly(True);self.candidates.setMaximumHeight(110);right.addWidget(self.candidates)
        self.confirmed=QLineEdit();self.confirmed.setPlaceholderText("Human-confirmed scientific name or category");right.addWidget(self.confirmed)
        self.reviewer=QLineEdit();self.reviewer.setPlaceholderText("Reviewer name (required)");right.addWidget(self.reviewer)
        self.review_note=QLineEdit();self.review_note.setPlaceholderText("Review note (optional)");right.addWidget(self.review_note)
        actions=QHBoxLayout();actions.addWidget(button("Confirm label",lambda:self.review_record("verified"),True));actions.addWidget(button("Reject prediction",lambda:self.review_record("rejected")));right.addLayout(actions)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(panel);splitter.addWidget(scroll);splitter.setSizes([550,550]);layout.addWidget(splitter,1);self.stack.addWidget(page)

    def make_reports(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label("Survey reporting", "title"));layout.addWidget(label("Descriptive camera summaries, reviewed records and encounter-hour tables. Reports use the current camera, verification and encounter-gap filters.","subtitle",True))
        actions=QHBoxLayout();actions.addWidget(button("Export PDF",self.export_pdf,True));actions.addWidget(button("Export offline HTML",self.export_html));actions.addWidget(button("Export observations CSV",self.export_csv));actions.addStretch();layout.addLayout(actions)
        self.report_preview=QTextBrowser();self.report_preview.setOpenExternalLinks(False);layout.addWidget(self.report_preview,1);self.stack.addWidget(page)

    def error(self,message):
        QMessageBox.warning(self,"Wildlitics",str(message))

    def require(self,idle=False):
        if not self.project:
            self.error("Open or create a project first.");return False
        if idle and self.worker is not None:
            self.error("A job is running. Wait for it or cancel it first.");return False
        return True

    def load_project(self,folder):
        if self.worker is not None:
            self.error("Finish or cancel the current job before changing projects.");return
        try:
            next_project=Project(folder)
            if self.project:self.project.close()
            self.project=next_project
            self.project_title.setText(self.project.name)
            self.project_hint.setText(str(self.project.folder))
            self.project_subtitle.setText("SYNTHETIC DEMO · Generated images and fixture predictions" if self.project.setting("synthetic_demo")=="true" else "Local project · original media preserved · human review required")
            self.ai_python.setText(self.project.setting("ai_python",default_ai_python()))
            self.reviewer.setText(self.project.setting("reviewer",""))
            self.refresh()
            self.statusBar().showMessage("Project opened: "+str(self.project.folder))
        except Exception as exc:self.error(exc)

    def new_project(self):
        if self.worker is not None:return self.error("Finish or cancel the current job first.")
        folder=QFileDialog.getExistingDirectory(self,"Choose a new project folder")
        if not folder:return
        if (Path(folder)/"wildlitics.sqlite").exists():return self.load_project(folder)
        name,ok=QInputDialog.getText(self,"Project name","Survey / project name:",text=Path(folder).name)
        if ok:
            try:
                project=Project(folder,create=True,name=name);project.close();self.load_project(folder)
            except Exception as exc:self.error(exc)

    def open_project(self):
        folder=QFileDialog.getExistingDirectory(self,"Open Wildlitics project")
        if folder:self.load_project(folder)

    def demo_project(self):
        if self.worker is not None:return self.error("Finish or cancel the current job first.")
        parent=QFileDialog.getExistingDirectory(self,"Choose where to create the synthetic demo")
        if not parent:return
        folder=Path(parent)/("Wildlitics-demo-"+datetime.now().strftime("%Y%m%d-%H%M%S"))
        try:self.load_project(create_demo(folder))
        except Exception as exc:self.error(exc)

    def add_camera(self):
        if not self.require(True):return
        folder=QFileDialog.getExistingDirectory(self,"Select one camera image folder")
        if not folder:return
        name,ok=QInputDialog.getText(self,"Camera ID","Unique camera ID:",text=Path(folder).name)
        if not ok:return
        try:self.project.add_camera(name,folder);self.refresh();self.scan()
        except Exception as exc:self.error(exc)

    def add_collection(self):
        if not self.require(True):return
        folder=QFileDialog.getExistingDirectory(self,"Select the parent folder containing one subfolder per camera")
        if not folder:return
        added,errors=0,[]
        for source in sorted(Path(folder).iterdir()):
            if source.is_dir() and not source.name.startswith('.'):
                try:self.project.add_camera(source.name,source);added+=1
                except ValueError as exc:errors.append(source.name+": "+str(exc))
        self.refresh()
        if errors:self.error("Some folders were skipped:\n"+"\n".join(errors[:12]))
        if added:self.scan()
        elif not errors:self.error("No camera subfolders found. Use Add camera folder for a single camera.")

    def deployment(self):
        if not self.require(True):return
        index=self.camera_table.currentRow()
        if index<0:return self.error("Select a camera row first.")
        camera=self.project.cameras()[index]
        start,ok=QInputDialog.getText(self,"Deployment start","ISO local date/time, e.g. 2026-10-01T00:00:00. Both dates can be empty.",text=camera['started'] or '')
        if not ok:return
        end,ok=QInputDialog.getText(self,"Deployment end","ISO local date/time:",text=camera['ended'] or '')
        if ok:
            try:self.project.set_deployment(camera['id'],start,end);self.refresh()
            except Exception as exc:self.error(exc)

    def start_work(self,fn,done):
        self.worker=Work(fn,self);self.worker.line.connect(self.log.appendPlainText);self.worker.done.connect(done)
        self.worker.failed.connect(self.job_error);self.worker.finished.connect(self.work_finished)
        self.run_button.setEnabled(False);self.cancel_button.setEnabled(True);self.worker.start()

    def work_finished(self):
        worker=self.worker;self.worker=None
        if worker:worker.deleteLater()
        self.run_button.setEnabled(True);self.cancel_button.setEnabled(False)

    def job_error(self,message):
        if self.current_run and self.project:
            self.project.finish_run(self.current_run,"failed",message);self.current_run=None
        self.ai_state.setText("Job failed. Original media were not edited.");self.log.appendPlainText(message)
        self.refresh();self.error(message)

    def cancel_job(self):
        if self.worker:
            self.worker.cancelled.set();self.ai_state.setText("Stopping the current job… saved predictions remain available for resume.")

    def scan(self):
        if not self.require(True):return
        folder=self.project.folder
        def work(worker):
            project=Project(folder)
            try:
                totals=[]
                for camera in project.cameras():
                    if worker.cancelled.is_set():break
                    worker.line.emit("Reading "+camera['name'])
                    totals.append(project.scan_camera(camera['id'],progress=lambda n,total,name:worker.line.emit(f"{camera['name']}: {n}/{total} · {name}"),cancelled=worker.cancelled.is_set))
                return totals
            finally:project.close()
        self.start_work(work,lambda result:(self.refresh(),self.statusBar().showMessage("Folder scan finished: "+json.dumps(result))))

    def browse_python(self):
        file,_=QFileDialog.getOpenFileName(self,"Select AI environment Python",self.ai_python.text(),"Python executable (python.exe python3 python);;All files (*)")
        if file:self.ai_python.setText(file)

    def check_runtime(self):
        if not self.require(True):return
        executable=self.ai_python.text().strip();self.project.set_setting("ai_python",executable)
        log=self.project.folder/'runs'/'runtime-check.log'
        self.ai_state.setText("Checking the selected AI environment…")
        self.start_work(lambda w:run_process(runtime_command(executable),log,cancelled=w.cancelled,on_line=w.line.emit),
                        lambda r:self.ai_state.setText("Runtime ready." if r['returncode']==0 else "Runtime check failed. Read the log and AI setup guide."))

    def start_ai(self):
        if not self.require(True):return
        try:
            run=self.project.prepare_run(self.camera_filter.currentData(),country=self.country.currentData(),
                threshold=self.threshold.value(),model=self.model.currentData(),all_images=self.reprocess.isChecked())
            self.run_ai(run)
        except Exception as exc:self.error(exc)

    def resume_ai(self):
        if not self.require(True):return
        ident=self.run_history.currentData()
        if not ident:return self.error("No saved inference job is selected.")
        try:
            run=self.project.run(ident)
            if run['kind']!='speciesnet':raise ValueError("Imported results are not resumable inference jobs")
            params=json.loads(run['parameters'])
            for item in params['media']:
                if not Path(item['path']).is_file() or file_hash(item['path'])!=item['sha256']:
                    raise ValueError("A job input changed or is missing: "+item['path'])
            self.run_ai(run)
        except Exception as exc:self.error(exc)

    def run_ai(self,run):
        executable=self.ai_python.text().strip();command=command_for_run(executable,run)
        self.project.set_setting('ai_python',executable);self.current_run=run['id']
        params=json.loads(run['parameters']);params.update(ai_python=executable,expected_speciesnet_package='5.0.6')
        with self.project.db:self.project.db.execute("UPDATE runs SET status='running',error=NULL,finished_utc=NULL,parameters=? WHERE id=?",(json.dumps(params),run['id']))
        self.log.clear();self.navigate(2);self.ai_state.setText("Running local wildlife AI. First use can take time to download the model.")
        def work(worker):
            log=Path(run['folder'])/'inference.log'
            check=run_process(runtime_command(executable),log,cancelled=worker.cancelled,on_line=worker.line.emit)
            if check['returncode']!=0:return check
            return run_process(command,log,cancelled=worker.cancelled,on_line=worker.line.emit)
        self.start_work(work,self.ai_done)

    def ai_done(self,result):
        run=self.project.run(self.current_run);path=Path(run['folder'])/'predictions.json';summary=''
        try:
            if path.exists():summary=json.dumps(self.project.import_predictions(path,run_id=run['id']))
            state='cancelled' if result['cancelled'] else 'complete' if result['returncode']==0 and path.exists() else 'failed'
            self.project.finish_run(run['id'],state,None if state=='complete' else result['tail'])
            self.ai_state.setText(f"Job {state}. {summary} All new predictions require human review.")
        except Exception as exc:
            self.project.finish_run(run['id'],'failed',str(exc));self.ai_state.setText("Could not import results: "+str(exc))
        self.current_run=None;self.refresh()

    def import_predictions(self):
        if not self.require(True):return
        file,_=QFileDialog.getOpenFileName(self,"Import SpeciesNet run_model JSON","","JSON files (*.json)")
        if not file:return
        try:
            result=self.project.import_predictions(file);self.refresh();self.ai_state.setText(json.dumps(result));self.navigate(3)
        except Exception as exc:self.error(exc)

    def setup_guide(self):
        QMessageBox.information(self,"Local AI setup",
            "The desktop interface and wildlife AI use separate environments.\n\n"
            "1. Install Python 3.12 from python.org.\n"
            "2. Run the supplied Install-AI.cmd (Windows), or scripts/setup_ai.py from source. It installs CPU PyTorch and SpeciesNet 5.0.6 locally.\n"
            "3. Select that environment's Python here and click Check runtime.\n"
            "4. Import camera folders and click Run wildlife AI. First inference downloads the official model. Later inference can use its local cache.\n\n"
            "The standard SpeciesNet cascade uses its upstream MegaDetector model. It is independent of the original Wildlitics 2.3.3 MDV6 configuration. No account/API key is configured by this prototype.")

    def open_project_files(self):
        if self.require():QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.project.folder)))

    def refresh(self):
        if not self.project:return
        selected=self.camera_filter.currentData();self.camera_filter.blockSignals(True);self.camera_filter.clear()
        cameras=self.project.cameras();self.camera_filter.addItem(f"All cameras ({len(cameras)})",None)
        for camera in cameras:self.camera_filter.addItem(camera['name'],camera['id'])
        index=self.camera_filter.findData(selected);self.camera_filter.setCurrentIndex(max(0,index));self.camera_filter.blockSignals(False)
        fill(self.camera_table,[(r['name'],r['folder'],r['images'],r['pending'] or 0,r['failed'] or 0,r['started'],r['ended'])for r in cameras])
        selected_run=self.run_history.currentData();self.run_history.clear()
        for run in self.project.runs():self.run_history.addItem(f"{run['created_utc']} · {run['kind']} · {run['status']} · {run['id'][:8]}",run['id'])
        index=self.run_history.findData(selected_run)
        if index>=0:self.run_history.setCurrentIndex(index)
        self.refresh_views()

    def refresh_views(self,*args):
        if not self.project:return
        selected=self.camera_filter.currentData();gap=self.gap.currentData()
        data=self.project.analysis(selected,gap_minutes=gap,verified_only=self.verified.isChecked())
        for widget,value in zip(self.metrics,[data['registered_cameras'],data['images'],data['review_states'].get('verified',0),data['review_states'].get('unreviewed',0)]):widget.setText(str(value))
        self.taxon_bars.set_values(data['taxon_labels'].items());self.hour_bars.set_values([(str(i),v)for i,v in enumerate(data['activity_hours'])])
        fill(self.coverage,[(r['name'],r['images'],r['labelled_observations'],r['processing_states'].get('pending',0),r['processing_states'].get('failed',0))for r in data['cameras']])
        self.quality.setText(f"Showing {data['selected_cameras']} of {data['registered_cameras']} registered cameras. Capture times missing on {data['observations_missing_capture_time']} eligible observations. Declared deployment durations assume continuous operation; validate downtime separately.")
        self.rows=self.project.observations(selected);self.review_table.blockSignals(True)
        fill(self.review_table,[(r['camera_name'],r['confirmed_taxon'] or r['taxon'] or r['common_name'] or 'Unresolved',f"{r['model_score']:.3f}" if r['model_score']is not None else '—',r['review_state'])for r in self.rows]);self.review_table.blockSignals(False)
        self.photo.show_observation(None);self.report_preview.setHtml(report_html(self.project,camera_id=selected,gap_minutes=gap,verified_only=self.verified.isChecked()))

    def select_observation(self):
        index=self.review_table.currentRow()
        if index<0 or index>=len(self.rows):return
        row=self.rows[index];self.photo.show_observation(row)
        self.confirmed.setText(row['confirmed_taxon'] or row['taxon'] or row['common_name'] or '')
        self.review_note.setText(row['note'] or '')
        self.observation_details.setText(f"{Path(row['path']).name} · {row['camera_name']} · Scope: {row['scope']} · Rank: {row['rank'] or 'unresolved'}\nDecision: {row['decision_source'] or 'detector only'} · Time: {row['captured'] or 'unknown'}")
        self.candidates.setPlainText('\n'.join(f"{c['taxon'].get('scientific_name') or c['taxon'].get('common_name') or c['taxon']['raw_label']}: {c['classifier_score']:.4f}" for c in json.loads(row['candidates'])) or 'No classifier candidates. This may be an unclassified detection.')

    def review_record(self,state):
        if not self.require(True):return
        index=self.review_table.currentRow()
        if index<0:return self.error('Select a prediction first.')
        try:
            self.project.review(self.rows[index]['id'],state,self.confirmed.text(),self.reviewer.text(),self.review_note.text())
            self.project.set_setting('reviewer',self.reviewer.text().strip());self.refresh_views()
            if self.review_table.rowCount():self.review_table.selectRow(min(index+1,self.review_table.rowCount()-1))
        except Exception as exc:self.error(exc)

    def export_path(self,suffix):
        if not self.require(True):return None
        folder=self.project.folder/'exports';folder.mkdir(exist_ok=True)
        suggested=folder/('Wildlitics-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.'+suffix)
        path,_=QFileDialog.getSaveFileName(self,'Export report',str(suggested),f'{suffix.upper()} files (*.{suffix})')
        if not path:return None
        if Path(path).exists():self.error('Choose a new filename; existing exports are preserved.');return None
        return path

    def export_html(self):
        path=self.export_path('html')
        if path:
            try:write_report(self.project,path,camera_id=self.camera_filter.currentData(),gap_minutes=self.gap.currentData(),verified_only=self.verified.isChecked());self.statusBar().showMessage('Saved '+path)
            except Exception as exc:self.error(exc)

    def export_csv(self):
        path=self.export_path('csv')
        if path:
            try:export_observations(self.project,path,self.camera_filter.currentData(),verified_only=self.verified.isChecked());self.statusBar().showMessage('Saved '+path)
            except Exception as exc:self.error(exc)

    def export_pdf(self):
        path=self.export_path('pdf')
        if path:
            try:
                writer=QPdfWriter(path);writer.setTitle(self.project.name+' · Wildlitics');writer.setResolution(144)
                document=QTextDocument();document.setDefaultFont(QFont('Segoe UI',10))
                document.setHtml(report_html(self.project,camera_id=self.camera_filter.currentData(),gap_minutes=self.gap.currentData(),verified_only=self.verified.isChecked()))
                document.print_(writer);self.statusBar().showMessage('Saved '+path)
            except Exception as exc:self.error(exc)

    def closeEvent(self,event):
        if self.worker is not None:
            self.error('Cancel the active job and wait for it to stop before closing.');event.ignore();return
        if self.project:self.project.close()
        event.accept()


def main():
    parser=argparse.ArgumentParser(description='Wildlitics local desktop prototype')
    parser.add_argument('--project',type=Path);parser.add_argument('--demo',type=Path,help='Create a new synthetic six-camera demo project')
    args=parser.parse_args()
    if args.demo:args.project=create_demo(args.demo)
    app=QApplication(sys.argv[:1]);app.setApplicationName('Wildlitics');app.setStyleSheet(STYLE)
    window=MainWindow(args.project)
    if app.primaryScreen():
        area=app.primaryScreen().availableGeometry()
        window.resize(min(1440,max(1060,area.width()-40)),min(940,max(680,area.height()-50)))
    window.show();return app.exec()


if __name__=='__main__':
    raise SystemExit(main())
